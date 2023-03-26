import re
import glob
import json
import argparse
import os

import networkx as nx
from scipy.sparse import coo_array, block_diag
from tqdm import tqdm

from verilog_to_graph import parser, grapher

def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-d',
        '--dataset-path',
        default='verilog_dataset',
        help='path to the verilog dataset directory'
    )
    parser.add_argument(
        '-p',
        '--prefix',
        default='combcirc',
        help='output file names prefix'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print out additional information'
    )
    args = parser.parse_args()

    return args

def get_reliability(json_filepath: str):
    json_data = ''
    with open(json_filepath, 'r') as ifile:
        json_data = ifile.read()

    # Fix improper json formatting
    json_data = re.sub(r',(\s+)}', r'\1}', json_data)
    graph_info = json.loads(json_data)

    return graph_info['reliability']

def main():
    args = parse_args()

    num_graphs = len(list(glob.iglob(f'{args.dataset_path}/*/*/*.v')))
    block_diag_adj_mat = coo_array((0, 0))
    graph_indicator = []
    graph_labels = []

    n_lbl_types = ['x', 'f', 'assign', 'and', 'or', 'xor', 'not', 'nand', 'nor', 'xnor', 'module0RandLevel', ' ']
    n_lbl_to_id = {n_lbl_types[i]: i for i in range(len(n_lbl_types))}
    node_labels = []

    with tqdm(total=num_graphs) as pbar:
        for i, filepath in enumerate(glob.iglob(f'{args.dataset_path}/*/*/*.v')):
            pbar.set_description_str(filepath)
            # if args.verbose:
                # print(f'{i+1:5}/{num_graphs:5}: Processing file {filepath}')

            reliability = get_reliability(f'{filepath[:-2]}.json')

            in_n, out_n, nodes, edges = parser(filepath)
            DG = grapher(in_n, out_n, nodes, edges)

            adj_mat = nx.to_scipy_sparse_array(DG, format='coo')

            block_diag_adj_mat = block_diag((block_diag_adj_mat, adj_mat))
            graph_indicator.extend([i for _ in range(adj_mat.shape[0])])
            graph_labels.append(reliability)

            if ' ' in DG.nodes:
                print("found ' ' in", filepath)
            if 'module0RandLevel' in DG.nodes:
                print("found 'module0RandLevel' in", filepath)

            labels = [re.sub(r'^(.+?)\d+$', r'\1', n) for n in DG.nodes]
            node_labels.extend([n_lbl_to_id[lbl] for lbl in labels])

            pbar.update(1)

    num_edges = block_diag_adj_mat.count_nonzero()
    num_nodes = block_diag_adj_mat.shape[0]

    if not os.path.exists(args.prefix):
        os.makedirs(args.prefix)

    with open(f'{args.prefix}/{args.prefix}_A.txt', 'w') as ofile:
        n = 0
        for edge in zip(block_diag_adj_mat.row, block_diag_adj_mat.col):
            ofile.write(f'{edge[0] + 1}, {edge[1] + 1}\n')
            n += 1

        assert n == num_edges

    with open(f'{args.prefix}/{args.prefix}_graph_indicator.txt', 'w') as ofile:
        n = 0
        for graph_i in graph_indicator:
            ofile.write(f'{graph_i + 1}\n')
            n += 1

        assert n == num_nodes

    with open(f'{args.prefix}/{args.prefix}_graph_labels.txt', 'w') as ofile:
        n = 0
        for val in graph_labels:
            ofile.write(f'{val}\n')
            n += 1

        assert n == num_graphs

    with open(f'{args.prefix}/{args.prefix}_node_labels.txt', 'w') as ofile:
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
