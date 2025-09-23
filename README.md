# setup
first you need to install `micromamba` or `mamba`

then you need to create the env (you can change the -n to change the name).
go to the root folder of this repo and run:
```bash
micromamba env create -f environment.yml -n cqdev
```

then you need to activate it
```bash
micromamba activate cqdev
```

now to open cq-editor just run
```bash
cq-editor
```
