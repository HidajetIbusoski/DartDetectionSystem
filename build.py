"""
Build script — convenience wrapper for PyInstaller.

Usage:
    python build.py
"""

import subprocess
import sys
import os


def main():
    print("=" * 60)
    print("  OfflineDarts — Build Standalone Application")
    print("=" * 60)
    print()

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Ensure assets directory exists
    os.makedirs("assets/sounds", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Generate sounds if they don't exist
    sounds_dir = os.path.join("assets", "sounds")
    if not os.path.exists(os.path.join(sounds_dir, "dart_hit.wav")):
        print("Generating sound effects...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from audio.sounds import _generate_all_sounds
        _generate_all_sounds()
        print("✓ Sound effects generated")

    # Run PyInstaller
    print()
    print("Building with PyInstaller...")
    print("-" * 60)

    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "offline_darts.spec",
        "--noconfirm",
        "--clean",
    ])

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("  ✓ Build complete!")
        print("  Output: dist/OfflineDarts/OfflineDarts.exe")
        print("=" * 60)
    else:
        print()
        print("✗ Build failed! Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
