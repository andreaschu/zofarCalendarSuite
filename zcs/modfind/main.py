from zcs.data.xmlutil import Questionnaire
from tkinter.filedialog import askopenfilename
from zcs.data.xmlutil import read_questionnaire
import networkx as nx
from typing import Tuple, Dict, List


def get_cal_modules(q: Questionnaire,
                    cal_page_uid: str = 'calendar',
                    mod_prefix_len: int = 2) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    def _get_mod_pages(g: nx.DiGraph, calendar_page_uid: str) -> list:
        # determine all pages as module page candidates that can be reached via a single transition from the calendar page
        candidates = [v for u, v in g.edges if u == calendar_page_uid]
        return [candidate for candidate in candidates if
                any([path for path in nx.all_simple_paths(g, candidate, calendar_page_uid)])]

    def _create_di_graph(questionnaire: Questionnaire) -> nx.DiGraph:
        g = nx.DiGraph()
        for page in questionnaire.pages:
            for transition in page.transitions:
                g.add_edge(page.uid, transition.target_uid)
        return g

    def _mod_prefix_dict(pages: list, prefix_len: int) -> dict:
        # create a set with all module prefixes
        mod_prefixes = {page_uid[:prefix_len] for page_uid in pages}

        # iterate over all module prefixes and add pages that start with them to the dictionary of module pages
        dict_of_modules = {
            mod_prefix: [page for page in pages if page.startswith(mod_prefix)] for mod_prefix in mod_prefixes}

        return dict_of_modules

    di_graph = _create_di_graph(q)

    # determine all those candidates that have at least one simple path back to the calendar
    list_of_mod_pages = _get_mod_pages(di_graph, cal_page_uid)
    dictionary_of_modules = _mod_prefix_dict(list_of_mod_pages, mod_prefix_len)

    dict_of_submodules = _mod_prefix_dict(list_of_mod_pages, mod_prefix_len + 1)

    return dictionary_of_modules, dict_of_submodules


def main():
    input_xml = askopenfilename()

    modules_dict, submodules_dict = get_cal_modules(read_questionnaire(input_xml), 'calendar', 3)

    print()


if __name__ == '__main__':
    main()
