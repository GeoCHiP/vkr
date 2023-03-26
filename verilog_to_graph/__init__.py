import argparse

from .verilog_parser import parser
from .grapher import grapher


def main():
    cli = argparse.ArgumentParser(description="Convert Gate level verilog to a graph")
    cli.add_argument('verilog_file', type=str, help="Path to the verilog file")

    args = cli.parse_args()

    in_n, out_n, nodes, edges = parser(args.verilog_file)
    G = grapher(in_n, out_n, nodes, edges)

    print(G.nodes())
    print(G.edges())

    for n, nbrsdict in G.adjacency():
        print(n, end=": ")
        for nbr, eattr in nbrsdict.items():
            print(nbr, end=' ')

        print()

if __name__ == '__main__':
    main()
