# River Erosion Mod (Fabric 1.20.1)

Tu naudoji TLauncher ir nori tiesiog įmesti modą į `mods` aplanką — šitas projektas tam paruoštas.

## Greitas naudojimas (TLauncher)
1. TLauncher'yje pasirink **Fabric 1.20.1** (su įdiegtu Fabric loader).
2. Susibuildink modą komanda:
   - `JAVA_HOME=$HOME/.local/share/mise/installs/java/21.0.2 PATH=$JAVA_HOME/bin:$PATH gradle clean build`
3. Paimk failą iš:
   - `build/libs/river-erosion-mod-<versija>.jar`
4. Įmesk tą `.jar` į savo Minecraft `mods` folderį.
5. Paleisk žaidimą su tuo pačiu **Fabric 1.20.1** profiliu.

## Konfigūracija (upės vingiavimas)
Paleidus žaidimą, susikurs:
- `config/river_erosion.json`

Redaguok šiuos laukus:
- `meanderFrequency`
- `meanderAmplitude`
- `meanderTimeScale`
- `erosionChance`
- `attemptsPerPlayer`

## Svarbi pastaba
Šitas modas yra **Minecraft 1.20.1 + Fabric**. Jei naudoji kitą versiją, reikės pertaikyti `build.gradle` priklausomybes.
