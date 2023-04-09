# ACME Certificate Extract

This tool is meant to export the certificates fetched by ACME for example through [Træfik](https://traefik.io/traefik/) to reuse them.

*This tool is compatible with Træfik v1 and v2. It also supports ACME v1 and v2.*


## Running the tool

The tool is written in `Python` and `Docker` – and can be used by running `docker run -v $(pwd)/acme:/acme -v $(pwd)/certs:/certs devopsansiblede/acme_certs_extract`.

This development repository does also provide a `docker-compose.yml` file to start the tool localy with the latest changes through `docker-compose up -d`.  
*Be aware that the `acme_example.json` present within this repository contains a nonsense example, that will brick every regular usage of it within a real certificate usecase. It is only meant to exist for testing purposes within this tool.*


## Configuration

The basic configuration can be used without special configuration. These are the variables to change default config:

*Boolean values within the variables must be noted in Python style, so `True` or `False`!*

| ENV Variable | Default Value | Description |
| ------------ | ------------- | ----------- |
| `ACMEFILE`   | `acme.json`   | Filename of the acme file to be analyzed – may be adjusted to your needs |
| `ACMEDIR`    | `/acme`       | Directory where the script is searching for the `ACMEFILE`, so don't forget to bind / mount something here – may be changed |
| `CERTSDIR`   | `/certs`      | Directory where the script will store the decoded certificate files, so don't forget to bind / mount something here – may be changed. |
| `CERTSPLIT`  | `-----BEGIN CERTIFICATE-----`| **Do not change** |
| `COLOR_ERROR` | `1;31`    | ANSI Color settings for error messages |
| `COLOR_INFO` | `0`        | ANSI Color settings for information messages |
| `COLOR_SUCCESS` | `0;32`  | ANSI Color settings for success messages |
| `COLOR_WARN` | `0;33`     | ANSI Color settings for warning messages |
| `CRT_ARCHIVE` | `True`       | Switch for deactivating or activating the certificate archive |
| `DEBUG`      | `False`       | Switch on debug mode – that will print (error) messages and not stay quiet |
| `REPLACE_ASTERISK` | `STAR`  | The asterisk `*` should not be part of filenames – so we'll replace it by this string.<br/>*Although the URL is converted to lowercase, this string is used without further modification.* |
| `STORE_FLAT_CRTS` | `True`   | Switch for deactivating or activating the storage of flat certificates. Flat intends all certificates to be in one folder `flat`, not separated by directories by domain. |
| `LIMIT_FQDN` | –             | If you want to limit the FQDNs to be watched, you can pass a comma separated list of them here; e. g. `foo.example.com,bar.example.com` |
| `EXCLUDE_FQDN` | –           | Counterpart of `LIMIT_FQDN` – comma separated list of FQDNs that should not be reflected; e. g. `foo.example.com,bar.example.com`. |
| `RUN_SCRIPT` | –             | Mount a bash script – e. g. `check.sh` – into the directory `${WORKDIR}` and set its name as value of `RUN_SCRIPT` (no leading `/`, has to be mounted directly into `${WORKDIR}`) – then every time, the certificates were changed, this script will be executed. Useful if you want to restart some Docker containers after certificates changed (You have to mount the Docker sock, etc ...) |
| `WORKDIR`    | `/certs_extract` | **Do not change** unless you build the container from scratch ... |


### ANSI Colors

The color settings above use only the numeric values – the control characters (`\u001b` in the beginning and `m` at the end) are added by the script.

A color string consists out of one to three (or even more) entities:

* the style entity, e.g. `0` for the default or `1` for bold style
* the foreground color, starting with a `3` – e.g. `31` for the color red
* the background color, starting with a `4` – e.g. `43` for the color yellow

With the default colors, we only change at most the foreground colors and styles, so our defaults consist out of one or two entities.

For more information on ANSI Color codes please head over to [Haoyi's Programming Blog](https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html).


## The Certs directory structure

Within the `CERTSDIR` folder, which should be binded or mounted, the following structure will be created:

* a subdirectory `certs` which will hold all certificates sorted by URLs. There will be a directory for the main URL and also for all SANs. Each URL directory contains these files:
  * `privkey.pem` as the file that contains the private key
  * `cert.pem` as the file that contains (only) the certificate for the URL
  * `chain.pem` as the file that contains the chain for the URL certificate
  * `fullchain.pem` as combined file that contains the certificate and the chain
* a subdirectory `flat` which does not contain any subdirectory structure – but holds all current certificates. There are four files for every URL:
  * `<URL>.key` same as `privkey.pem` above
  * `<URL>.crt` same as `cert.pem` above
  * `<URL>.chain.pem` same as `chain.pem` above
  * `<URL>_full.crt` same as `fullchain.pem` above
* a subdirectory `archive` that holds subdirectories for all domains – and below that you'll find a date structure (Python format `%Y%m%d%H%M%S`) with all archived certificates

The creation of certificates below `certs` cannot be switched off. For `archive` and `flat` directories, use the ENV `CRT_ARCHIVE` and `STORE_FLAT_CRTS` variables above if you do not want them to be created.


## License

This project is published unter [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) license.


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## last built

2023-04-09 23:19:57
