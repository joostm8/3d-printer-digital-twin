# gcode_append_m400.py

def append_m400_to_movements(input_file, output_file):
    """
    Reads a G-code file and appends 'M400' after every movement command (G0, G00, G1, G01).
    """
    movement_cmds = {"G0", "G00", "G1", "G01"}
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            stripped = line.strip()
            if any(stripped.startswith(cmd) for cmd in movement_cmds):
                outfile.write(stripped + '\n')
                outfile.write('M114\n')
                outfile.write('M400\n')
            else:
                outfile.write(stripped + '\n')

if __name__ == "__main__":
    input_path = "vase.gcode"
    output_path = "vase-m114.gcode"
    append_m400_to_movements(input_path, output_path)
    print(f"Modified G-code written to {output_path}")
