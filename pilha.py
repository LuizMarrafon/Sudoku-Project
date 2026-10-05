class Pilha:
    def __init__(No):
        No.topo = None

    def push(No, no):
        no.proximo = No.topo
        No.topo = no

    def pop(No):
        no = No.topo
        if no is not None:
            No.topo = no.proximo
            no.proximo = None
        return no

    def isEmpty(No):
        return No.topo is None
