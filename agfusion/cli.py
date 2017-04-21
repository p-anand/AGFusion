import sqlite3
import os
import sys
import argparse
import logging
import urllib
import gzip
import shutil

import agfusion
import pyensembl

def annotate(gene5prime,junction5prime,gene3prime,junction3prime,
             outdir,colors,rename,scale,db,pyensembl_data,args):


    fusion = agfusion.Fusion(
        gene5prime=gene5prime,
        gene5primejunction=junction5prime,
        gene3prime=gene3prime,
        gene3primejunction=junction3prime,
        db=db,
        pyensembl_data=pyensembl_data,
        protein_databases=args.protein_databases,
        noncanonical=args.noncanonical
    )

    fusion.save_transcript_cdna(
        out_dir=outdir,
        middlestar=args.middlestar
    )
    fusion.save_transcript_cds(
        out_dir=outdir,
        middlestar=args.middlestar
    )
    fusion.save_proteins(
        out_dir=outdir,
        middlestar=args.middlestar
    )

    fusion.save_images(
        out_dir=outdir,
        scale=scale,
        colors=colors,
        rename=rename,
        fontsize=args.fontsize,
        height=args.height,
        width=args.width,
        dpi=args.dpi,
        no_domain_labels=args.no_domain_labels,
        plot_WT=args.WT
        )

def builddb(args):

    db = agfusion.AGFusionDBBManager(args.database, args.build, args.server)

    db.logger.info('Fetching alternative gene names...')

    db.fetch_gene_names()

    db.logger.info('Fetching transcript tables...')

    db.fetch_transcript_table()

    db.fetch_refseq_table()

    db.logger.info('Fetching protein annotation data...')

    db.fetch_protein_annotation()

def add_common_flags(parser):
    parser.add_argument(
        '-o',
        '--out',
        type=str,
        required=True,
        help='Directory to save results'
    )
    parser.add_argument(
        '-g',
        '--genome',
        type=str,
        required=True,
        help='Pick one of the following: GRCh38 (for hg38), ' +
             'GRCh37 (for hg19), or GRCm38 (for mm10). Or enter ' +
             'the Ensembl MySQL database name (e.g. homo_sapiens_core_84_38 for GRCm38).'
    )
    parser.add_argument(
        '--noncanonical',
        action='store_true',
        required=False,
        default=False,
        help='(Optional) Include non-canonical gene transcripts ' +
             'in the analysis (default False).'
    )
    parser.add_argument(
        '--protein_databases',
        type=str,
        required=False,
        nargs='+',
        default=['Pfam', 'transmembrane'],
        help='(Optional) Space-delimited list of one or more protein ' +
             'feature databases to include when visualizing proteins. ' +
             'Options are: Pfam, Smart, Superfamily, TIGRfam, Prosite_profiles, ' +
             'transmembrane, low_complexity, coiled_coil, Prints ' +
             'PIRSF, and signal_peptide ' +
             '(default includes Pfam and transmembrane).'
    )
    parser.add_argument(
        '--recolor',
        type=str,
        required=False,
        default=None,
        action='append',
        help='(Optional) Re-color a domain. Provide the original name of the domain then your color (semi-colon delimited, all in quotes). Can specify --recolor multiples for each domain. (e.g. --color \"Pkinase_Tyr;blue\" --color \"I-set;#006600\").'
    )
    parser.add_argument(
        '--rename',
        type=str,
        required=False,
        default=None,
        action='append',
        help='(Optional) Rename a domain. Provide the original name of the domain then your new name (semi-colon delimited, all in quotes). Can specify --rename multiples for each domain. (e.g. --rename \"Pkinase_Tyr;Kinase\").'
    )
    parser.add_argument(
        '--type',
        type=str,
        required=False,
        default='png',
        help='(Optional) Image file type (png, jpeg, pdf). Default: png'
    )
    parser.add_argument(
        '-w',
        '--width',
        type=int,
        required=False,
        default=10,
        help='(Optional) Image width in inches (default 10).'
    )
    parser.add_argument(
        '-ht',
        '--height',
        type=int,
        required=False,
        default=3,
        help='(Optional) Image file height in inches (default 3).'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        required=False,
        default=None,
        help='(Optional) Dots per inch.'
    )
    parser.add_argument(
        '--fontsize',
        type=int,
        required=False,
        default=12,
        help='(Optional) Fontsize (default 12).'
    )
    parser.add_argument(
        '--WT',
        action='store_true',
        required=False,
        help='(Optional) Include this to plot wild-type architechtures of the 5\' and 3\' genes'
    )
    parser.add_argument(
        '--middlestar',
        action='store_true',
        required=False,
        help='(Optional) Insert a * at the junction position for the cdna, cds, and protein sequences (default False).'
    )
    parser.add_argument(
        '--no_domain_labels',
        action='store_true',
        required=False,
        help='(Optional) Do not label domains.'
    )
    parser.add_argument(
        '--db',
        type=str,
        default=None,
        required=False,
        help='(Optional) The SQLite3 database. Defaults to using the ' +
             'database provided by the package.'
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=agfusion.__version__
    )

def main():

    parser = argparse.ArgumentParser(
        description='Annotate Gene Fusion (AGFusion)'
    )
    subparsers = parser.add_subparsers(help='AGFusion programs.',dest="subparser_name")

    annotate_parser = subparsers.add_parser('annotate', help='Annotate and visualize a single fusion.')
    annotate_parser.add_argument(
        '-g5',
        '--gene5prime',
        type=str,
        required=True,
        help='5\' gene partner'
    )
    annotate_parser.add_argument(
        '-g3',
        '--gene3prime',
        type=str,
        required=True,
        help='3\' gene partner'
    )
    annotate_parser.add_argument(
        '-j5',
        '--junction5prime',
        type=int,
        required=True,
        help='Genomic location of predicted fuins for the 5\' gene partner. ' +
             'The 1-based position that is the last nucleotide included in ' +
             'the fusion before the junction.'
    )
    annotate_parser.add_argument(
        '-j3',
        '--junction3prime',
        type=int,
        required=True,
        help='Genomic location of predicted fuins for the 3\' gene partner. ' +
             'The 1-based position that is the first nucleotide included in ' +
             'the fusion after the junction.'
    )
    add_common_flags(annotate_parser)
    annotate_parser.add_argument(
        '--scale',
        type=int,
        required=False,
        default=None,
        help='(Optional) Set maximum width (in amino acids) of the figure to rescale the fusion (default: max length of fusion product)'
    )

    # batch file parser

    batch_parser = subparsers.add_parser('batch', help='Annotate fusions from an output file from a fusion finding algorithm.')
    batch_parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Output file from fusion-finding algorithm.'
    )
    #batch_parser.add_argument(
    #    '--algorithm',
    #    type=str,
    #    required=True,
    #    help='The fusion-finding algorithm. Can be one of the following: ' +
    #         'bellerphontes, breakfusion, chimerascan, ericscript, ' +
    #         'fusioncatcher, fusionhunter, fusionmap, jaffa, mapsplice, ' +
    #         'nfuse, soapfuse, or tophatfusion.'
    #)
    batch_parser.add_argument(
        '-a',
        '--algorithm',
        type=str,
        required=True,
        help='The fusion-finding algorithm. Can be one of the following: ' +
             'fusioncatcher. (Will support more algorithms soon)'
    )
    add_common_flags(batch_parser)

    # download database parser

    database_parser = subparsers.add_parser('database', help='Download database for a reference genome.')
    database_parser.add_argument(
        '--database',
        type=str,
        required=True,
        help='Path to the database file (e.g. agfusion.db)'
    )
    database_parser.add_argument(
        '--build',
        type=str,
        required=True,
        help='homo_sapiens_core_84_38 (for GRCh38), ' +
        'homo_sapiens_core_75_37 (for GRCh37), or ' +
        'mus_musculus_core_84_38 (for GRCm38)'
    )
    database_parser.add_argument(
        '--server',
        type=str,
        required=False,
        default='ensembldb.ensembl.org',
        help='(optional) Ensembl server (default ensembldb.ensembl.org)'
    )
    args = parser.parse_args()

    if args.subparser_name == 'database':
        builddb(args)
    else:
        if not os.path.exists(args.out):
            os.mkdir(args.out)

        # if user does not specify a sqlite database then use the one provided
        # by the package

        if args.db is None:
            file_path = os.path.join(
                os.path.split(__file__)[0],
                'data',
                'agfusion.db'
            )

            db = agfusion.AGFusionDB(
                file_path
            )
        else:
            db = agfusion.AGFusionDB(args.db)

        # get the pyensembl data

        if args.genome == 'GRCm38' or args.genome == 'mus_musculus_core_84_38':
            pyensembl_data = pyensembl.EnsemblRelease(84, 'mouse')
            db.build = 'mus_musculus_core_84_38'
        elif args.genome == 'GRCh38' or args.genome == 'homo_sapiens_core_84_38':
            pyensembl_data = pyensembl.EnsemblRelease(84, 'human')
            db.build = 'homo_sapiens_core_84_38'
        elif args.genome == 'GRCh37' or args.genome == 'homo_sapiens_core_75_37':
            pyensembl_data = pyensembl.EnsemblRelease(75, 'human')
            db.build = 'homo_sapiens_core_75_37'
        else:
            db.logger.error(
                'You provided an incorrect reference genome. '
                'Use one of the following: GRCh38, GRCh37, or GRCm38'
            )
            sys.exit()

        colors = {}
        rename = {}

        if args.recolor is not None:
            for i in args.recolor:
                pair = i.split(';')

                assert len(pair) == 2, " did not properly specify --colors"

                if pair[0] in colors:
                    print "!!! WARNING - you specified colors for %s twice." % pair[0]

                colors[pair[0]] = pair[1]

        if args.rename is not None:
            for i in args.rename:
                pair = i.split(';')

                assert len(pair) == 2, " did not properly specify --rename"

                if pair[0] in rename:
                    print "!!! WARNING - you rename %s twice." % pair[0]

                rename[pair[0]] = pair[1]

        if args.subparser_name == 'annotate':
            annotate(
                gene5prime=args.gene5prime,
                junction5prime=args.junction5prime,
                gene3prime=args.gene3prime,
                junction3prime=args.junction3prime,
                outdir=args.out,
                colors=colors,
                rename=rename,
                scale=args.scale,
                db=db,
                pyensembl_data=pyensembl_data,
                args=args
            )
        else:
            if args.algorithm in agfusion.parsers:
                for fusion in agfusion.parsers[args.algorithm](args.file):

                    outdir = os.path.join(
                        args.out,
                        fusion['alternative_name_5prime'] + '-' +
                        str(fusion['junction_5prime']) + '_' +
                        fusion['alternative_name_3prime'] + '-' +
                        str(fusion['junction_3prime'])
                    )

                    if not os.path.exists(outdir):
                        os.mkdir(outdir)
                    else:
                        db.logger.warn('The following output directory already exists! %s' % outdir)

                    annotate(
                        gene5prime=fusion['ensembl_5prime'],
                        junction5prime=fusion['junction_5prime'],
                        gene3prime=fusion['ensembl_3prime'],
                        junction3prime=fusion['junction_3prime'],
                        outdir=outdir,
                        colors=colors,
                        rename=rename,
                        scale=None,
                        db=db,
                        pyensembl_data=pyensembl_data,
                        args=args
                    )
