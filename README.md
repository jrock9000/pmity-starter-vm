# PMITY Starter class VM

Downloads of the ready-made class virtual machine (VM) for **Your First Platform on One Machine**, the one-day PMITY Starter
course (`pmity-starter-00-meetup`). The course page is at https://pmity.com/starter/.

## Get the VM

1. Open the newest release: https://github.com/jrock9000/pmity-starter-vm/releases/latest
2. Download **every** `pmity-lab.ova.part*` file, `pmity-lab.ova.sha256`, and the assemble script for your computer:
   - Windows: `pmity-assemble-vm.bat`
   - Linux or Intel Mac: `pmity-assemble-vm.sh`
3. Put them all in one folder and run the script there (Windows: double-click the `.bat`; Linux/macOS: `bash pmity-assemble-vm.sh`).
   It checks every piece, tells you if one is missing or damaged, joins them into `pmity-lab.ova` and checks the result.
4. Import `pmity-lab.ova` into VirtualBox (File, Import Appliance). Follow the course page's "Before class" steps from there.

The image is for Intel and AMD (x86-64) computers. On an Apple-silicon Mac, follow the course page's Apple-silicon path instead.

## How it is made

Each release is built from scratch on GitHub's own build machine by `.github/workflows/vm-release.yml`, from the course's
build scripts (`ova/build-ova.sh`, `ova/update-ova.sh`), and boot-tested by `ova/test-ova.sh` before anything is published.
The release tag is `starter-vm-` followed by the first 12 characters of the `.ova` file's SHA-256 checksum.
