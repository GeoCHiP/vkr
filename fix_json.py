import re
import glob
from pathlib import Path

from tqdm import tqdm


def main():
    with tqdm(total=len(glob.glob('verilog_dataset/*/*/*.json'))) as pbar:
        for filepath in glob.iglob('verilog_dataset/*/*/*.json'):
            pbar.set_description(filepath)

            json_data = Path(filepath).read_text()

            # Fix improper json formatting
            json_data = re.sub(r',(\s*)}', r'\1}', json_data)

            Path(filepath).write_text(json_data)

            pbar.update(1)



if __name__ == '__main__':
    main()
