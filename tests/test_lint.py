import json
from pathlib import Path
import subprocess
import sys
import unittest

from relayscl_lint import scan_xml, scan_file

ROOT = Path(__file__).resolve().parents[1]


class SCLLintTests(unittest.TestCase):
    def codes(self, file):
        return {item.code for item in scan_file(ROOT / "examples" / file)}

    def test_valid_synthetic_example(self):
        self.assertEqual(self.codes("valid.scd"), set())

    def test_bad_reference_and_address(self):
        codes = self.codes("broken.scd")
        for expected in ("GSE004", "GSE005", "COM007", "COM010", "COM013"):
            self.assertIn(expected, codes)

    def test_namespace_free(self):
        xml = b'<SCL><IED name="R"><AccessPoint name="AP"><Server><LDevice inst="LD"><LN0><DataSet name="D"><FCDA/></DataSet><GSEControl name="G" datSet="D" confRev="1"/></LN0></LDevice></Server></AccessPoint></IED></SCL>'
        self.assertEqual({f.code for f in scan_xml(xml)}, {"COM001"})

    def test_malformed_xml(self):
        self.assertIn("XML001", {f.code for f in scan_xml(b"<SCL>")})

    def test_wrong_root(self):
        self.assertIn("SCL001", {f.code for f in scan_xml(b"<Other/>")})

    def test_read_failure(self):
        self.assertIn("IO001", {f.code for f in scan_file(ROOT / "does-not-exist.cid")})

    def test_cli_json_pass(self):
        out = subprocess.run([sys.executable, str(ROOT / "relayscl_lint.py"),
                              "--format", "json", str(ROOT / "examples" / "valid.scd")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)
        self.assertEqual(json.loads(out.stdout)["reports"][0]["summary"]["error"], 0)

    def test_cli_json_error(self):
        out = subprocess.run([sys.executable, str(ROOT / "relayscl_lint.py"),
                              "--format", "json", str(ROOT / "examples" / "broken.scd")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertGreater(json.loads(out.stdout)["reports"][0]["summary"]["error"], 0)

    def test_duplicate_control(self):
        xml = b'<SCL><IED name="R"><AccessPoint name="A"><Server><LDevice inst="L"><LN0><DataSet name="D"><FCDA/></DataSet><GSEControl name="x" datSet="D" confRev="1"/><GSEControl name="x" datSet="D" confRev="1"/></LN0></LDevice></Server></AccessPoint></IED></SCL>'
        self.assertIn("GSE002", {f.code for f in scan_xml(xml)})

    def test_unmatched_mapping(self):
        xml = b'<SCL><Communication><SubNetwork name="x"><ConnectedAP iedName="I" apName="A"><GSE ldInst="LD" cbName="g"/></ConnectedAP></SubNetwork></Communication></SCL>'
        codes = {f.code for f in scan_xml(xml)}
        self.assertIn("COM002", codes)
        self.assertIn("COM004", codes)


if __name__ == "__main__":
    unittest.main()
