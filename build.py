import os
import sys
import subprocess
import shutil
from fontTools.ttLib import TTFont, newTable
from fontTools.otlLib.builder import buildStatTable

# Paths
project_dir = r"D:\dev\Playfair-Mono"
config_path = os.path.join(project_dir, "sources", "config.yaml")
venv_bin = os.path.join(project_dir, ".venv", "Scripts")
gftools_path = os.path.join(venv_bin, "gftools.exe")
gftools_fix_font_path = os.path.join(venv_bin, "gftools-fix-font.exe")
python_path = os.path.join(venv_bin, "python.exe")

roman_font_path = os.path.join(project_dir, "fonts", "variable", "PlayfairMono[opsz,wght].ttf")
italic_font_path = os.path.join(project_dir, "fonts", "variable", "PlayfairMono-Italic[opsz,wght].ttf")

def add_stat_table(font_path, is_italic=False):
    print(f"Adding STAT table and meta table to: {font_path}")
    font = TTFont(font_path)
    
    # Define axes and values (only registered fallbacks in Google Fonts Axis Registry)
    opsz_values = [
        dict(value=6, name="6pt"),
        dict(value=7, name="7pt"),
        dict(value=8, name="8pt"),
        dict(value=12, name="12pt"),
        dict(value=16, name="16pt"),
        dict(value=48, name="48pt"),
        dict(value=72, name="72pt"),
        dict(value=96, name="96pt"),
    ]
    
    wght_values = [
        dict(value=300, name="Light"),
        dict(value=400, name="Regular", flags=2, linkedValue=700),
        dict(value=500, name="Medium"),
        dict(value=600, name="SemiBold"),
        dict(value=700, name="Bold"),
        dict(value=800, name="ExtraBold"),
        dict(value=900, name="Black"),
    ]
    
    if is_italic:
        ital_values = [
            dict(value=1, name="Italic")
        ]
    else:
        ital_values = [
            dict(value=0, name="Roman", flags=2, linkedValue=1)
        ]
        
    axes = [
        dict(
            tag="opsz",
            name="Optical size",
            ordering=0,
            values=opsz_values
        ),
        dict(
            tag="wght",
            name="Weight",
            ordering=1,
            values=wght_values
        ),
        dict(
            tag="ital",
            name="Italic",
            ordering=2,
            values=ital_values
        )
    ]
    
    buildStatTable(font, axes, elidedFallbackName="Regular")
    
    # Inject meta table
    meta = font["meta"] = newTable("meta")
    meta.data = {
        "dlng": "Latn, Cyrl",
        "slng": "Latn, Cyrl"
    }
    print("  Injecting meta table...")
    
    font.save(font_path)
    print("  Post-processing completed successfully.")

def main():
    # 1. Update PATH to include virtualenv Scripts directory so ninja/fontmake work
    os.environ["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
    
    # 2. Run gftools builder
    print("Step 1: Running gftools builder...")
    # Clean output fonts dir
    fonts_dir = os.path.join(project_dir, "fonts")
    if os.path.exists(fonts_dir):
        shutil.rmtree(fonts_dir)
        
    cmd = [python_path, "-m", "gftools.builder", config_path]
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=project_dir)
    if res.returncode != 0:
        print("Error: gftools builder failed.")
        sys.exit(res.returncode)
    print("gftools builder completed successfully.\n")

    # 3. Post-process with gftools-fix-font (with correct double-quoted default axis values on Windows)
    print("Step 2: Fixing default axis values and metadata...")
    for font_path in [roman_font_path, italic_font_path]:
        if not os.path.exists(font_path):
            print(f"Error: Expected font file not found: {font_path}")
            sys.exit(1)
            
        cmd = [gftools_fix_font_path, "-o", font_path, "--fvar-instance-axis-dflts", "opsz=12 wght=400", font_path]
        print(f"Executing: {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=project_dir)
        if res.returncode != 0:
            print(f"Error: gftools-fix-font failed on {font_path}")
            sys.exit(res.returncode)
    print("gftools-fix-font completed successfully.\n")

    # 4. Inject STAT table
    print("Step 3: Injecting custom STAT tables...")
    add_stat_table(roman_font_path, is_italic=False)
    add_stat_table(italic_font_path, is_italic=True)
    print("STAT table injection completed successfully.\n")
    
    print("Build and post-processing completed successfully!")

if __name__ == "__main__":
    main()
