import networkx as nx

def grapher(in_n, out_n, nodes, edges):

    # in_n, out_n, nodes, edges = verilog_parser.parser(file_)

    G=nx.DiGraph()
    G.add_nodes_from(in_n)
    G.add_nodes_from(out_n)
    G.add_nodes_from(nodes)


    for i in edges:
        for j in i[2]:
            G.add_edge(i[1], j)

    return G
