import sys

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process command line options.')
  parser.add_argument('--version', action='version', version='0')
  args = parser.parse_args()
