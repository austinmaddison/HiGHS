#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Assemble XCFramework from static libraries"
    )
    parser.add_argument(
        "--device-lib", 
        required=True, 
        help="Path to device library (.a file)"
    )
    parser.add_argument(
        "--sim-libs", 
        required=True, 
        help="Comma-separated paths to simulator libraries (.a files)"
    )
    parser.add_argument(
        "--name", 
        required=True, 
        help="Name of the XCFramework"
    )
    parser.add_argument(
        "--out", 
        required=True, 
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse simulator libraries
    sim_libs = [lib.strip() for lib in args.sim_libs.split(",")]
    
    # Build xcodebuild command
    xcframework_path = output_dir / f"{args.name}.xcframework"
    cmd = [
        "xcodebuild",
        "-create-xcframework",
        "-library", args.device_lib
    ]
    
    # Add simulator libraries
    for sim_lib in sim_libs:
        cmd.extend(["-library", sim_lib])
    
    # Add output path
    cmd.extend(["-output", str(xcframework_path)])
    
    try:
        # Execute xcodebuild command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Wrote {xcframework_path}")
        
        # Print xcodebuild output if verbose
        if result.stdout:
            print("xcodebuild output:")
            print(result.stdout)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running xcodebuild: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: xcodebuild not found. Make sure Xcode is installed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
