#!/usr/bin/env python3
"""
Teknova App Icon Generator
Generates all required iOS app icon sizes from SVG/template
"""

import os
import subprocess
from pathlib import Path

# Icon sizes for iOS (width in pixels)
IOS_ICON_SIZES = {
    "Icon-20@2x.png": 40,
    "Icon-20@3x.png": 60,
    "Icon-29@2x.png": 58,
    "Icon-29@3x.png": 87,
    "Icon-40@2x.png": 80,
    "Icon-40@3x.png": 120,
    "Icon-60@2x.png": 120,
    "Icon-60@3x.png": 180,
    "Icon-1024.png": 1024,
}

def create_icon_svg():
    """Generate SVG content for Teknova logo"""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#127A50"/>
      <stop offset="100%" style="stop-color:#3B6DF2"/>
    </linearGradient>
    <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#F1B538"/>
      <stop offset="100%" style="stop-color:#FFC84F"/>
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect width="1024" height="1024" rx="230" fill="url(#bgGradient)"/>
  
  <!-- Inner glow circle -->
  <circle cx="512" cy="480" r="280" fill="white" fill-opacity="0.15"/>
  
  <!-- AI Eye - Outer -->
  <ellipse cx="512" cy="420" rx="200" ry="110" fill="none" stroke="white" stroke-width="18"/>
  
  <!-- AI Eye - Pupil -->
  <circle cx="512" cy="420" r="55" fill="white"/>
  
  <!-- Scanning line -->
  <rect x="320" y="415" width="384" height="10" rx="5" fill="url(#accentGradient)"/>
  
  <!-- Paw Print -->
  <g transform="translate(512, 620)" fill="url(#accentGradient)">
    <!-- Main pad -->
    <ellipse cx="0" cy="40" rx="65" ry="55"/>
    <!-- Toes -->
    <ellipse cx="-70" cy="-20" rx="30" ry="35" transform="rotate(-15)"/>
    <ellipse cx="-25" cy="-50" rx="28" ry="32" transform="rotate(-5)"/>
    <ellipse cx="25" cy="-50" rx="28" ry="32" transform="rotate(5)"/>
    <ellipse cx="70" cy="-20" rx="30" ry="35" transform="rotate(15)"/>
  </g>
  
  <!-- Teknova Text (subtle) -->
  <text x="512" y="880" text-anchor="middle" font-family="SF Pro Rounded, -apple-system, sans-serif" 
        font-size="72" font-weight="700" fill="white" fill-opacity="0.9" letter-spacing="8">
    TEKNOVA
  </text>
</svg>'''
    return svg

def generate_png_icons(output_dir):
    """Generate PNG icons using sips (macOS built-in)"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save SVG
    svg_path = output_path / "icon_source.svg"
    with open(svg_path, 'w') as f:
        f.write(create_icon_svg())
    
    print(f"✅ SVG source saved to: {svg_path}")
    
    # Try to convert using different methods
    success = False
    
    # Method 1: Try using qlmanage (macOS Quick Look)
    try:
        # First convert SVG to PNG at max size
        temp_png = output_path / "temp_1024.png"
        result = subprocess.run([
            'qlmanage', '-t', '-s', '1024', '-o', str(output_path), str(svg_path)
        ], capture_output=True, text=True, timeout=30)
        
        # qlmanage adds .png to the output
        ql_output = output_path / f"{svg_path.stem}.svg.png"
        if ql_output.exists():
            ql_output.rename(temp_png)
            success = True
    except Exception as e:
        print(f"⚠️ qlmanage failed: {e}")
    
    # Method 2: Try using ImageMagick if available
    if not success:
        try:
            temp_png = output_path / "temp_1024.png"
            subprocess.run([
                'convert', '-background', 'none', '-density', '300',
                str(svg_path), '-resize', '1024x1024', str(temp_png)
            ], check=True, timeout=30)
            success = True
        except Exception as e:
            print(f"⚠️ ImageMagick not available: {e}")
    
    # Method 3: Create a simple colored icon using sips
    if not success:
        print("📝 Creating fallback icon using CoreGraphics...")
        create_fallback_icon(output_path)
        success = True
        temp_png = output_path / "temp_1024.png"
    
    if success and temp_png.exists():
        # Resize to all needed sizes using sips
        for filename, size in IOS_ICON_SIZES.items():
            output_file = output_path / filename
            try:
                subprocess.run([
                    'sips', '-z', str(size), str(size),
                    str(temp_png), '--out', str(output_file)
                ], check=True, capture_output=True, timeout=30)
                print(f"✅ Created: {filename} ({size}x{size})")
            except Exception as e:
                print(f"❌ Failed to create {filename}: {e}")
        
        # Clean up temp file
        if temp_png.exists():
            temp_png.unlink()
    
    # Create Contents.json
    contents_json = create_contents_json()
    with open(output_path / "Contents.json", 'w') as f:
        f.write(contents_json)
    print(f"✅ Contents.json updated")
    
    return output_path

def create_fallback_icon(output_path):
    """Create a simple gradient icon using Python PIL"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        size = 1024
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle background with gradient effect
        for i in range(size):
            # Gradient from green (#127A50) to blue (#3B6DF2)
            r = int(18 + (59 - 18) * i / size)
            g = int(122 + (109 - 122) * i / size)
            b = int(80 + (242 - 80) * i / size)
            draw.line([(0, i), (size, i)], fill=(r, g, b, 255))
        
        # Add rounded corners
        corner_radius = 230
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (size, size)], corner_radius, fill=255)
        img.putalpha(mask)
        
        # Draw white eye shape
        eye_center = (512, 420)
        eye_rx, eye_ry = 200, 110
        draw.ellipse([
            eye_center[0] - eye_rx, eye_center[1] - eye_ry,
            eye_center[0] + eye_rx, eye_center[1] + eye_ry
        ], outline=(255, 255, 255, 255), width=18)
        
        # Draw pupil
        pupil_r = 55
        draw.ellipse([
            eye_center[0] - pupil_r, eye_center[1] - pupil_r,
            eye_center[0] + pupil_r, eye_center[1] + pupil_r
        ], fill=(255, 255, 255, 255))
        
        # Draw scanning line (gold color)
        draw.rectangle([320, 415, 704, 425], fill=(241, 181, 56, 255))
        
        # Draw paw print
        paw_color = (241, 181, 56, 255)
        paw_center = (512, 660)
        # Main pad
        draw.ellipse([
            paw_center[0] - 65, paw_center[1] - 15,
            paw_center[0] + 65, paw_center[1] + 95
        ], fill=paw_color)
        # Toes
        toe_positions = [(-70, -60), (-25, -90), (25, -90), (70, -60)]
        for dx, dy in toe_positions:
            cx, cy = paw_center[0] + dx, paw_center[1] + dy
            draw.ellipse([cx - 28, cy - 32, cx + 28, cy + 32], fill=paw_color)
        
        # Try to add text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/SFNSRounded.ttf", 72)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
            except:
                font = ImageFont.load_default()
        
        # Draw TEKNOVA text
        text = "TEKNOVA"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((size - text_width) // 2, 820), text, fill=(255, 255, 255, 230), font=font)
        
        # Save
        img.save(output_path / "temp_1024.png", "PNG")
        print("✅ Fallback icon created with PIL")
        
    except ImportError:
        print("⚠️ PIL not available, creating minimal icon...")
        create_minimal_icon(output_path)

def create_minimal_icon(output_path):
    """Create a minimal icon using just basic tools"""
    # Create a simple solid color icon as fallback
    import struct
    import zlib
    
    def create_png(width, height, color):
        """Create a simple solid color PNG"""
        def png_chunk(chunk_type, data):
            chunk_len = len(data)
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xffffffff
            return struct.pack('>I', chunk_len) + chunk + struct.pack('>I', crc)
        
        # PNG signature
        signature = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = png_chunk(b'IHDR', ihdr_data)
        
        # IDAT chunk (image data)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # Filter type: None
            for x in range(width):
                raw_data += bytes(color[:3])  # RGB
        
        compressed = zlib.compress(raw_data, 9)
        idat = png_chunk(b'IDAT', compressed)
        
        # IEND chunk
        iend = png_chunk(b'IEND', b'')
        
        return signature + ihdr + idat + iend
    
    # Create a teal/green colored icon
    png_data = create_png(1024, 1024, (18, 122, 80))  # #127A50
    
    with open(output_path / "temp_1024.png", 'wb') as f:
        f.write(png_data)
    print("✅ Minimal icon created")

def create_contents_json():
    """Create Contents.json for Xcode asset catalog"""
    return '''{
  "images" : [
    {
      "filename" : "Icon-20@2x.png",
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "20x20"
    },
    {
      "filename" : "Icon-20@3x.png",
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "20x20"
    },
    {
      "filename" : "Icon-29@2x.png",
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "29x29"
    },
    {
      "filename" : "Icon-29@3x.png",
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "29x29"
    },
    {
      "filename" : "Icon-40@2x.png",
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "40x40"
    },
    {
      "filename" : "Icon-40@3x.png",
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "40x40"
    },
    {
      "filename" : "Icon-60@2x.png",
      "idiom" : "iphone",
      "scale" : "2x",
      "size" : "60x60"
    },
    {
      "filename" : "Icon-60@3x.png",
      "idiom" : "iphone",
      "scale" : "3x",
      "size" : "60x60"
    },
    {
      "filename" : "Icon-1024.png",
      "idiom" : "ios-marketing",
      "scale" : "1x",
      "size" : "1024x1024"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}'''

if __name__ == "__main__":
    # Output to the iOS project's Assets folder
    script_dir = Path(__file__).parent
    output_dir = script_dir / "ios" / "AIAnimalTracking" / "AIAnimalTracking" / "Assets.xcassets" / "AppIcon.appiconset"
    
    print("🎨 Teknova App Icon Generator")
    print("=" * 40)
    
    result_path = generate_png_icons(output_dir)
    
    print("=" * 40)
    print(f"✅ Icons generated at: {result_path}")
    print("\n📱 Next steps:")
    print("1. Open Xcode")
    print("2. Select Assets.xcassets")
    print("3. Verify AppIcon shows all sizes")
    print("4. Build and run!")
