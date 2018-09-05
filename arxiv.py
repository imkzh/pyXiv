#!/usr/bin/python3

import sys
import time
import io

# arxiv protocols implementations
import xivapi
import oaipmh

import utils
import const

# data serialization and parsing
import re
import argparse
import json


def cmd_download(cmd, args, show_help_only=False):

    par = argparse.ArgumentParser(prog="arxiv " + cmd, add_help=False,
                                  description="Download arXiv articles by its ID or name.")

    par.add_argument("-o", "--output", type=str, default="./", required=False,
                     help="Output location for downloaded documents.")

    par.add_argument("-n", "--name", type=str, default="{id}.{title}", required=False,
                     help="Document namimg syntax. Available fields: {id}, {title}, {prim_author}, {category}.")

    par.add_argument("-m", "--meta-only", default=False, action="store_true",
                     help="Download metadata only (overrides -M)")

    par.add_argument("-M", "--no-meta", default=False, action="store_true",
                     help="Don't save metadata while downloding.")

    par.add_argument("article", metavar="ARTICLE", nargs="+",
                     help="Article IDs(like 1801.00001) or article title to download.")

    if show_help_only:
        par.print_help()
        print(" ")
        print('In addition, subcommand "get" is identical to "download".')
        return

    if cmd in ["get", "download"]:
        arg = par.parse_args(args)

        for each in arg.article:

            if xivapi.check_id(each):
                # download article by its id
                resp = xivapi.do_query(id_list=each, max_results=1)
                query = "id"
                prompt_name = "[arXiv:" + each + "]"
            else:
                resp = xivapi.do_query(search_query=each, max_results=1)
                query = "title"
                prompt_name = '"' + each + '"'

            if (resp is not None) and ("feed" in resp) and (resp["feed"] is not None):

                if len(resp["feed"]["entries"]) > 0:

                    for rl in resp["feed"]["entries"][0]["related-links"]:

                        if ("title" in rl) and ("pdf" in rl["title"]):
                            entry = resp["feed"]["entries"][0]

                            f_id = entry["url"].replace("://arxiv.org/abs/", "").replace("http", "").replace("https", "").replace("/", "-")
                            fname = arg.name.replace("{id}", f_id).replace("{title}", resp["feed"]["entries"][0]["title"])

                            if "authors" in entry and len(entry["authors"]) > 0:
                                fname = fname.replace("{auth_prim}", entry["authors"][0])
                            else:
                                fname = fname.replace("{auth_prim}", "N.A")

                            if "category" in entry and "term" in entry["category"]:
                                fname = fname.replace("{category}", entry["category"]["term"])
                            else:
                                fname = fname.replace("{category}", "no.cate")

                            fname = utils.filename_filter(fname)

                            if not arg.no_meta or arg.meta_only:
                                f_meta = io.open(arg.output + "/" + fname + ".metainfo.json", "w")
                                s = json.dumps(resp["feed"], indent=4)
                                f_meta.write(s + "\n")
                                f_meta.close()

                            if arg.meta_only:
                                break

                            print("Downloading:", fname)
                            time.sleep(3)
                            utils.download_file(rl["href"], arg.output + "/" + fname + ".pdf", user_agent=const.USER_AGENT)

                            print("[info]  article", prompt_name, "downloaded\n", "\t saved as:", fname + ".pdf")
                            break
                    else:
                        print("[Error] Failed to download", prompt_name + ":\n",
                              "\tserver refused to return the link to pdf of this article.")
                else:
                    print("[Error] Failed to download", prompt_name + ":\n", "\tno such article with this id.")

            else:
                print("[Error] Failed to download", prompt_name + ":\n", "\tno such article with this id.")


def cmd_query(cmd, args, show_help_only=False):

    if cmd == "search":
        par = argparse.ArgumentParser(prog="arxiv " + cmd, add_help=False,
                                      description="A simplified searching interface for subcommand query, search specified term in given scope.")

        par.add_argument("-s", "--scope", type=str, default="all", required=False,
                         help='Search scope, can be all(-sa), title, abstract, (default: all)')

        par.add_argument("-a", "--in-abstract", default=False, action="store_true",
                         help="equavalent to --scope=abstract")

        par.add_argument("-c", "--count", default=5, type=int,
                         help="record count per page.")

        par.add_argument("-p", "--page", default=1, type=int,
                         help="specifies which page to show.")

        par.add_argument("-o", "--output", type=str, default=None,
                         help="save metadata to disk.")

        par.add_argument("-n", "--name", default="{id}.{title}",
                         help="Document namimg syntax. Available fields: {id}, {title}. --output=./ is inferred.")

        par.add_argument("term", metavar="TERM", nargs="+", help="Seaching terms.")

        if show_help_only:
            par.print_help()
            return

        arg = par.parse_args(args)



    elif cmd == "query":

        par = argparse.ArgumentParser(prog="arxiv " + cmd, add_help=False,
                                      description="Query arXiv database for metadata.")

        par.add_argument("query", metavar="QUERY_STRING", nargs="+", help="arXiv query string, see: https://arxiv.org/help/api/user-manual#Appendices")

        if show_help_only:
            par.print_help()
            return

        arg = par.parse_args(args)
        query_string = " ".join(arg.query)



def cmd_show(cmd, args, show_help_only=False):
    par = argparse.ArgumentParser(prog="arxiv " + cmd, description="", add_help=False)

    if show_help_only:
        par.print_help()
        return

    arg = par.parse_args(args)

    pass


def cmd_oai(cmd, args, show_help_only=False):
    par = argparse.ArgumentParser(prog="arxiv " + cmd, description="", add_help=False)

    if show_help_only:
        par.print_help()
        return

    arg = par.parse_args(args)


def cmd_help(cmd, args):

    if args is None or len(args) == 0:

        print("usage: arxiv help [COMMAND_NAME]")
        print("available commands:")
        print(" ", "download - download articles.")
        print(" ", "show     - show metadata of a given article.")
        print(" ", "query    - do a arXiv query.")
        print(" ", "search   - search documents on arXiv.")
        print(" ", "list     - list articles matching a given query string.")
        print(" ", "oai      - metadata harvesting interface.")
        print(" ")

    else:

        if args[0] in ["download", "get"]:
            cmd_download(args[0], args, show_help_only=True)
        elif args[0] in ["show", "list", "search"]:
            cmd_query(args[0], args, show_help_only=True)
        elif args[0] in ["oai"]:
            cmd_oai(args[0], args, show_help_only=True)


def main():
    par = argparse.ArgumentParser(prog="arxiv", description="A simple CLI for searching, download, batch harvest, and analyse arxiv documents.")
    par.add_argument("command", metavar="COMMAND",
                     help="Currently available commands are: search, query, show, list, download, get, oai, help")
    par.add_argument("cmdargs", metavar="CMD_ARGS", type=str,
                     nargs='*', help="article name or id to download")

    args = par.parse_args()

    if args.command in ["download", "get"]:
        cmd_download(args.command, args.cmdargs)
    elif args.command in ["show", "list", "search", "query"]:
        cmd_query(args.command, args.cmdargs)
    elif args.command in ["oai", "pmh", "oaipmh"]:
        cmd_oai(args.command, args.cmdargs)
    elif args.command in ["help"]:
        cmd_help(args.command, args.cmdargs)
    else:
        print("arxiv: error: unsupported command:", args.command, file=sys.stderr)



if __name__ == '__main__':
    main()
