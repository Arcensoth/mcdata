# mcdata
Version-controlled history of Minecraft's generated data.

Since [Minecraft snapshot 18w01a](https://minecraft.net/en-us/article/minecraft-snapshot-18w01a) Mojang has exposed the game's internal data generators, allowing us to get a data-driven dump of commands, blocks, items, and all sorts of nice things.

This repository uses [mcgen](https://github.com/Arcensoth/mcgen) to invoke the server generators and process the output.

You can produce the raw data yourself by running the following command, replacing `{jar_path}` with the actual path to the server jar:

```bash
# Prior to 21w39a:
java -cp {jar_path} net.minecraft.data.Main --server --reports

# From 21w39a onward:
java -DbundlerMainClass=net.minecraft.data.Main -jar {jar_path} --server --reports
```

Server downloads can be found via Mojang's [version manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json).

## Disclaimer
*This repository is working under the assumption that, because they intentionally exposed their internal data generators, Mojang does not have anything against the resulting data existing somewhere on the internet for public consumption. If ever this assumption is contradicted, the repository will be promptly removed.*
