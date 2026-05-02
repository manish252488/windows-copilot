import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis desktop assistant")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Restart automatically when project .py files change (development)",
    )
    args = parser.parse_args()

    if getattr(sys, "frozen", False) and args.reload:
        print("Hot reload is not available in the packaged executable.", file=sys.stderr)
        sys.exit(2)

    observer = None
    if args.reload:
        from jarvis.dev_reload import start_dev_reload

        observer = start_dev_reload()

    from jarvis.ui.app import JarvisDesktopApp

    try:
        JarvisDesktopApp().run()
    finally:
        if observer is not None:
            observer.stop()
            observer.join(timeout=2)


if __name__ == "__main__":
    main()
