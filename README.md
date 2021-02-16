# ACME Certificate Extract

This tool is meant to export the certificates fetched by ACME for example through [Træfik](https://traefik.io/traefik/) to reuse them.

*This tool is compatible with Træfik v1 and v2. It also supports ACME v1 and v2.*


## Running the tool

The tool is written in `Python` and `Docker` – and can be used by running `docker run devopsansiblede/acme-cert-extract`. This development repository does also provid a `docker-compose.yml` file to start the tool localy with the latest changes through `docker-compose up -d`.

*Be aware that the `acme_example.json` present within this repository contains a nonsense example, that will brick every regular usage of it within a real certificate usecase. It is only meant to exist for testing purposes within this tool.*


## Configuration

The basic configuration can be used without special configuration. These are the variables to change default config:

| ENV Variable | Default Value | Description |
| ------------ | ------------- | ----------- |
| `ACMEFILE`   | `acme.json`   | Filename of the acme file to be analyzed – may be adjusted to your needs |
| `ACMEDIR`    | `/acme`       | Directory where the script is searching for the `ACMEFILE`, so don't forget to bind / mount something here – may be changed |
| `CERTSDIR`   | `/certs`      | Directory where the script will store the decoded certificate files, so don't forget to bind / mount something here – may be changed. |
| `CERTSPLIT`  | `-----BEGIN CERTIFICATE-----`| **Do not change** |
| `CRT_ARCHIVE` | `True`       | Switch for deactivating or activating the certificate archive |
| `DEBUG`      | `False`       | Switch on debug mode – that will print (error) messages and not stay quiet |
| `STORE_FLAT_CRTS` | `True`   | Switch for deactivating or activating the storage of flat certificates |
| `WORKDIR`    | `/certs_extract` | **Do not change** unless you build the container from scratch ... |


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
