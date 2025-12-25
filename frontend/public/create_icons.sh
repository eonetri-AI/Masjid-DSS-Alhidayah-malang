#!/bin/bash
# Create placeholder PWA icons using ImageMagick or convert

# Check if imagemagick is installed
if command -v convert &> /dev/null; then
    # Create 192x192 icon
    convert -size 192x192 xc:#0F172A \
            -gravity center \
            -fill white \
            -font DejaVu-Sans-Bold \
            -pointsize 100 \
            -annotate +0+0 "🕌" \
            icon-192x192.png 2>/dev/null || echo "ImageMagick not available"
    
    # Create 512x512 icon
    convert -size 512x512 xc:#0F172A \
            -gravity center \
            -fill white \
            -font DejaVu-Sans-Bold \
            -pointsize 300 \
            -annotate +0+0 "🕌" \
            icon-512x512.png 2>/dev/null || echo "ImageMagick not available"
else
    echo "ImageMagick not found. Creating placeholder files..."
    # Create minimal PNG files as placeholders
    echo "Please replace with actual icons"
fi
