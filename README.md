# mcdata
Version-controlled history of Minecraft's generated data.

Since [Minecraft snapshot 18w01a](https://minecraft.net/en-us/article/minecraft-snapshot-18w01a) Mojang has exposed the game's internal data generators, allowing us to get a data-driven dump of commands, blocks, items, and all sorts of nice things.

Run the following command on a server jar to invoke the exposed generators and produce data:

```bash
java -cp minecraft_server.*.jar net.minecraft.data.Main --all
```

## Disclaimer
*This repository is working under the assumption that, because they intentionally exposed their internal data generators, Mojang does not have anything against the resulting data existing somewhere on the internet for public consumption. If ever this assumption is contradicted, the repository will be promptly removed.*
