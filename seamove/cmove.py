"""
Continious move files from a to b
"""
# pylint: disable=logging-fstring-interpolation
import logging
import os
import shutil
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from concurrent.futures import ThreadPoolExecutor
from logging import ERROR, INFO, WARNING, FileHandler, getLogger
from pathlib import Path

from rich.logging import RichHandler
from rich.progress import Progress

from . import __version__

log = getLogger(__name__)


def cli():
    """
    Command line interface for cmove
    """
    # TODO: add log level/verbosity selection -v -vv
    #       quiet mode might be more useful -q -qq -qqq
    #       "disable info, disable warning, disable error"
    # TODO: add log to file option
    def dir_validator(directory: str) -> Path | None:
        """Test is dir and return Path object"""
        tmp = Path(directory).resolve()

        if tmp.is_dir():
            return tmp

        log.error(f"'{tmp!s}' is not a directory")
        return None

    parser = ArgumentParser(
        description=r"""
    cmove "Sea Move" an continious data mover

              \   |   /            _\/_
                .-'-.              //o\   _\/_
 __--__  _ --_ /     \ _--_ __  __ _ | __ /o\\ 
=-=-_=-=_=-_= -=======- = =-=_=-=_,-'|"'""-|-,
=-=-_=- _=-= _--=====- _=-=_-_,-"          |
-=--=- =-= =- = -  -==- --= - ."   [v{version}]""".format(
            version=__version__
        ),
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target",
        type=dir_validator,
        help="folder to move files from",
    )
    parser.add_argument(
        "destination",
        type=dir_validator,
        help="folder to move files to",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        help="time to sleep between loops/iterations/checks (sec)",
        default=None,
        metavar="N",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        help="number of concurrent workers/threads",
        default=None,
        metavar="N",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="reduce/supress log verbosity   ",
    )

    parser.add_argument(
        "-l",
        "--log",
        nargs="?",
        default=None,
        const="cmove.log",
        help="log to file",
    )

    return parser


def wait(seconds: int):
    """Wait for n sec, and show the wait progress"""
    if not seconds:
        return

    with Progress(transient=True,) as progress:
        task = progress.add_task("[cyan]Sleep ...", total=seconds)
        while not progress.finished:
            progress.update(task, advance=1)
            time.sleep(1)


def cmove(target: Path, destination: Path, threads=None) -> None:
    """_summary_

    Args:
        target (Path): _description_
        destination (Path): _description_
    """

    def _move(file, dest):
        """Move file from a to b and remove from a if already in b"""
        try:
            shutil.move(file, dest)
            log.info(f"'{file!s}' moved to destination, '{dest!s}'")

        except shutil.Error:
            # TODO: ensure same file
            log.warning(f"'{file!s}' already exist in destination, removing...")
            os.remove(file)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        for file in filter(os.path.isfile, map(str, target.glob("*"))):
            executor.submit(_move, file, destination)


def main():
    """
    cmove as a util
    """
    # Use the same fmts for all Handlers
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="[%Y-%m-%d %X]",
    )

    # Setup default CLI log
    consol_logger = RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=False,
        show_level=False,
    )
    consol_logger.setFormatter(formatter)

    log.addHandler(consol_logger)

    args = cli().parse_args()

    # If target or dest is missing exit
    if not (args.target and args.destination):
        raise SystemExit()

    log.setLevel({0: INFO, 1: WARNING}.get(args.quiet, ERROR))

    # Log to file if requested
    if logfile := args.log:
        file_logger = FileHandler(filename=logfile)
        file_logger.setFormatter(formatter)
        log.addHandler(file_logger)

    # Main loop
    try:
        while True:
            cmove(
                target=args.target, destination=args.destination, threads=args.threads
            )
            wait(seconds=args.sleep)

    except KeyboardInterrupt:
        raise SystemExit()  # pylint: disable=raise-missing-from


if __name__ == "__main__":
    main()
