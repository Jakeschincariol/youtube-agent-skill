from pathlib import Path
import tempfile
import unittest

from PySide6.QtGui import QImage

from animatube.assets.devops_diagrams import (
    DevOpsDiagramGenerator,
    generate_all_devops_diagrams,
)


class DevOpsDiagramTests(unittest.TestCase):
    def test_single_diagram_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            out_file = Path(temp_dir) / "term_test.png"
            gen = DevOpsDiagramGenerator(width=1920, height=1080)
            res = gen.generate_terminal_diagram(out_file)

            self.assertTrue(res.is_file())
            self.assertGreater(res.stat().st_size, 1000)

            # Read back with QImage to verify geometry and integrity
            img = QImage(str(res))
            self.assertFalse(img.isNull())
            self.assertEqual(img.width(), 1920)
            self.assertEqual(img.height(), 1080)

    def test_generate_all_devops_diagrams(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mapping = generate_all_devops_diagrams(temp_path)

            self.assertIn("pillars_overview", mapping)
            self.assertIn("terminal", mapping)
            self.assertIn("git_tree", mapping)
            self.assertIn("docker", mapping)
            self.assertIn("jenkins", mapping)
            self.assertIn("aws", mapping)

            for key, file_path in mapping.items():
                self.assertTrue(file_path.is_file(), f"Missing diagram: {key}")
                self.assertGreater(file_path.stat().st_size, 2000, f"File too small: {file_path}")


if __name__ == "__main__":
    unittest.main()
