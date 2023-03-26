import re
import glob
import json
import argparse
import os
from pathlib import Path

import networkx as nx
from scipy.sparse import coo_array, block_diag
from tqdm import tqdm

from verilog_to_graph import parser, grapher

def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-d',
        '--dataset-path',
        default='verilog_dataset',
        help='path to the verilog dataset directory',
    )
    parser.add_argument(
        '-p',
        '--prefix',
        default='combcirc',
        help='output file names prefix',
    )
    parser.add_argument(
        '-o',
        '--output-directory',
        default='combcirc',
        help='output files directory',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print out additional information',
    )
    args = parser.parse_args()

    return args

def get_reliability(json_filepath: str):
    json_data = Path(json_filepath).read_text()
    graph_info = json.loads(json_data)
    return graph_info['reliability']

def main():
    args = parse_args()

    num_graphs = len(list(glob.iglob(f'{args.dataset_path}/*/*/*.v')))
    block_diag_adj_mat = coo_array((0, 0))
    graph_indicator = []
    graph_labels = []

    n_lbl_types = ['x', 'f', 'assign', 'and', 'or', 'xor', 'not', 'nand', 'nor', 'xnor', ' ']
    n_lbl_to_id = {n_lbl_types[i]: i for i in range(len(n_lbl_types))}
    node_labels = []

    with tqdm(total=num_graphs) as pbar:
        for i, filepath in enumerate(glob.iglob(f'{args.dataset_path}/*/*/*.v')):
            pbar.set_description_str(filepath)

            reliability = get_reliability(f'{filepath[:-2]}.json')

            in_n, out_n, nodes, edges = parser(filepath)
            DG = grapher(in_n, out_n, nodes, edges)

            adj_mat = nx.to_scipy_sparse_array(DG, format='coo')

            block_diag_adj_mat = block_diag((block_diag_adj_mat, adj_mat))
            graph_indicator.extend([i for _ in range(adj_mat.shape[0])])
            graph_labels.append(reliability)

            if args.verbose and ' ' in DG.nodes:
                print("found ' ' in", filepath)

            labels = [re.sub(r'^(.+?)\d+$', r'\1', n) for n in DG.nodes]
            node_labels.extend([n_lbl_to_id[lbl] for lbl in labels])

            pbar.update(1)

    num_edges = block_diag_adj_mat.count_nonzero()
    num_nodes = block_diag_adj_mat.shape[0]

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    with open(f'{args.output_directory}/{args.prefix}_A.txt', 'w') as ofile:
        n = 0
        for edge in zip(block_diag_adj_mat.row, block_diag_adj_mat.col):
            ofile.write(f'{edge[0] + 1}, {edge[1] + 1}\n')
            n += 1

        assert n == num_edges

    with open(f'{args.output_directory}/{args.prefix}_graph_indicator.txt', 'w') as ofile:
        n = 0
        for graph_i in graph_indicator:
            ofile.write(f'{graph_i + 1}\n')
            n += 1

        assert n == num_nodes

    with open(f'{args.output_directory}/{args.prefix}_graph_labels.txt', 'w') as ofile:
        n = 0
        for val in graph_labels:
            ofile.write(f'{val}\n')
            n += 1

        assert n == num_graphs

    with open(f'{args.output_directory}/{args.prefix}_node_labels.txt', 'w') as ofile:
        n = 0
        for val in node_labels:
            ofile.write(f'{val}\n')
            n += 1

        assert n == num_nodes


    if args.verbose:
        print('Done.')
        print(f'Processed:')
        print(f'{num_graphs} graphs')
        print(f'{num_nodes} nodes')
        print(f'{num_edges} edges')


if __name__ == '__main__':
    main()
