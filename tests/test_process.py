import os
from pathlib import Path
import signal
import sys
import time
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from bounded_process import run


class ProcessTests(unittest.TestCase):
    def python(self, code, **kwargs):
        return run([sys.executable, '-B', '-c', code], **kwargs)

    def test_success_separate_streams_and_nonzero(self):
        result = self.python('import sys; print("out"); print("err", file=sys.stderr); sys.exit(7)')
        self.assertEqual((result.returncode, result.stdout, result.stderr, result.reason),
                         (7, b'out\n', b'err\n', 'exited'))

    def test_stdin_eof_and_literal_args(self):
        result = run([sys.executable, '-c', 'import sys; print(sys.argv[1]); print(len(sys.stdin.read()))',
                      '$(touch nope); "quotes"'])
        self.assertEqual(result.stdout, b'$(touch nope); "quotes"\n0\n')

    def test_floods_are_bounded(self):
        for fd, stream in [(1, 'stdout'), (2, 'stderr')]:
            result = self.python(f'import os\nwhile True: os.write({fd}, b"x"*65536)',
                                 stdout_limit=1234, stderr_limit=1234)
            self.assertEqual(result.reason, stream + '-limit')
            self.assertEqual(len(getattr(result, stream)), 1234)

    def test_both_pipes_do_not_deadlock(self):
        result = self.python('import os\nfor _ in range(128):\n os.write(1,b"a"*1024)\n os.write(2,b"b"*1024)',
                             stdout_limit=200000, stderr_limit=200000)
        self.assertEqual(result.reason, 'exited')
        self.assertEqual(len(result.stdout), 131072)
        self.assertEqual(len(result.stderr), 131072)

    def test_timeout_even_when_pipes_closed(self):
        start = time.monotonic()
        result = self.python('import os,time; os.close(1); os.close(2); time.sleep(20)', timeout=0.15)
        self.assertEqual(result.reason, 'timeout')
        self.assertLess(time.monotonic() - start, 2)

    def test_cancellation(self):
        start = time.monotonic()
        result = self.python('import time; time.sleep(20)',
                             cancelled=lambda: time.monotonic() - start > 0.15)
        self.assertEqual(result.reason, 'cancelled')
        self.assertLess(time.monotonic() - start, 2)

    def test_descendant_cleanup_after_leader_exit(self):
        for close_pipes in (False, True):
            code = ('import os,time\npid=os.fork()\nif pid == 0:\n'
                    + (' os.close(1); os.close(2)\n' if close_pipes else '')
                    + ' time.sleep(20)\nelse:\n print(pid,flush=True)\n')
            result = self.python(code, timeout=0.2)
            pid = int(result.stdout)
            self.assertEqual(result.reason, 'exited' if close_pipes else 'timeout')
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                path = Path(f'/proc/{pid}/stat')
                if not path.exists() or path.read_text().split()[2] == 'Z':
                    break
                time.sleep(0.01)
            else:
                self.fail(f'descendant {pid} still running')

    def test_invalid_budgets_and_missing_executable(self):
        for kwargs in ({'timeout': float('nan')}, {'timeout': 0}, {'stdout_limit': -1},
                       {'stderr_limit': True}):
            with self.assertRaises(ValueError):
                run(['/bin/true'], **kwargs)
        with self.assertRaises(ValueError):
            run('echo unsafe')
        with self.assertRaises(FileNotFoundError):
            run(['/definitely-missing-template-test-command'])

    def test_import_does_not_replace_handlers(self):
        result = self.python('import signal; before=signal.getsignal(signal.SIGTERM); '
                             f'import sys; sys.path.insert(0,{str(Path(__file__).resolve().parent.parent / "scripts")!r}); '
                             'import bounded_process; assert signal.getsignal(signal.SIGTERM)==before')
        self.assertEqual(result.returncode, 0)
