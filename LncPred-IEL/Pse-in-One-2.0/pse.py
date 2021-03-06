if __name__ == '__main__':
    import argparse
    import sys
    import subprocess
    from argparse import RawTextHelpFormatter

    parse = argparse.ArgumentParser(description="This is pse module for generate pse vector.",
                                    formatter_class=RawTextHelpFormatter)

    parse.add_argument('inputfiles', nargs='*',
                       help="The input files in FASTA format.")
    parse.add_argument('-out', nargs='*',
                       help="The output files for storing feature vectors.")
    parse.add_argument('alphabet', choices=['DNA', 'RNA', 'Protein'],
                       help="The alphabet of sequences.")
    parse.add_argument('method', type=str,
                       help="The method name of pseudo components.")

    parse.add_argument('-lamada', type=int, default=2,
                       help="The value of lamada. default=2")
    parse.add_argument('-w', type=float, default=0.1,
                       help="The value of weight. default=0.1")
    parse.add_argument('-k', type=int,
                       help="The value of kmer, it works only with PseKNC method.")
    parse.add_argument('-i',
                       help="The indices file user choose.\n"
                            "Default indices:\n"
                            "DNA dinucleotide: Rise, Roll, Shift, Slide, Tilt, Twist.\n"
                            "DNA trinucleotide: Dnase I, Bendability (DNAse).\n"
                            "RNA: Rise, Roll, Shift, Slide, Tilt, Twist.\n"
                            "Protein: Hydrophobicity, Hydrophilicity, Mass.")
    parse.add_argument('-e', help="The user-defined indices file.\n")
    parse.add_argument('-all_index', dest='a', action='store_true', help="Choose all physicochemical indices")
    parse.add_argument('-no_all_index', dest='a', action='store_false',
                       help="Do not choose all physicochemical indices, default.")
    parse.set_defaults(a=False)
    parse.add_argument('-f', default='tab', choices=['tab', 'svm', 'csv'],
                       help="The output format (default = tab).\n"
                            "tab -- Simple format, delimited by TAB.\n"
                            "svm -- The libSVM training data format.\n"
                            "csv -- The format that can be loaded into a spreadsheet program.")

    parse.add_argument('-labels', nargs='*',
                       help="The labels of the input files.\n"
                       "For binary classification problem, the labels can only be '+1' or '-1'.\n"
                       "For multiclass classification problem, the labels can be set as a list of integers.")

    args = parse.parse_args()
    sys.dont_write_bytecode = True
    cmder = ' '.join(sys.argv[1:])
    cmd = 'python psee.pyc' + ' ' + cmder
    subprocess.call(cmd, shell=True)
