package com.example.rivererosion;

/**
 * Universali (nuo API nepriklausoma) upės vingiavimo/erozijos logika.
 * <p>
 * Šį failą gali nukopijuoti į Fabric/Forge/NeoForge/Bukkit projektą ir
 * naudoti su bet kuria Minecraft Java versija, nes klasė neturi jokių
 * Minecraft importų.
 */
public final class RiverMeanderCore {

    private RiverMeanderCore() {
    }

    public static final class Settings {
        public double meanderFrequency = 0.06;
        public double meanderAmplitude = 1.8;
        public double meanderTimeScale = 0.003;
        public double erosionChance = 0.42;

        public Settings() {
        }
    }

    public static final class Flow {
        public final int flowX;
        public final int flowZ;
        public final int erodeBankX;
        public final int erodeBankZ;

        public Flow(int flowX, int flowZ, int erodeBankX, int erodeBankZ) {
            this.flowX = flowX;
            this.flowZ = flowZ;
            this.erodeBankX = erodeBankX;
            this.erodeBankZ = erodeBankZ;
        }
    }

    /**
     * Apskaičiuoja srovės kryptį ir krantą, kurį reikia ardyti.
     *
     * @param worldTime žaidimo laikas/tick'ai
     * @param x         bloko X
     * @param z         bloko Z
     * @param settings  vingiavimo parametrai
     */
    public static Flow computeFlow(long worldTime, int x, int z, Settings settings) {
        double angle = meanderAngle(worldTime, x, z, settings);

        int flowX = sign(Math.cos(angle));
        int flowZ = sign(Math.sin(angle));
        if (flowX == 0 && flowZ == 0) {
            flowX = 1;
        }

        // Statmena kryptis - eroduojamas krantas.
        int bankX = -flowZ;
        int bankZ = flowX;

        return new Flow(flowX, flowZ, bankX, bankZ);
    }

    /**
     * Deterministinis pseudo-random sprendimas ar šį tick'ą daryti eroziją.
     * Tinka kai nori stabilaus rezultato nepriklausomai nuo API random implementacijos.
     */
    public static boolean shouldErode(long seed, long worldTime, int x, int z, Settings settings) {
        long mixed = seed
                ^ (worldTime * 341873128712L)
                ^ (x * 132897987541L)
                ^ (z * 42317861L);
        mixed ^= (mixed >>> 33);
        mixed *= 0xff51afd7ed558ccdL;
        mixed ^= (mixed >>> 33);
        mixed *= 0xc4ceb9fe1a85ec53L;
        mixed ^= (mixed >>> 33);

        double unit = (mixed >>> 11) * 0x1.0p-53; // [0, 1)
        return unit < settings.erosionChance;
    }

    private static double meanderAngle(long worldTime, int x, int z, Settings settings) {
        double base = (x + z) * settings.meanderFrequency;
        double time = worldTime * settings.meanderTimeScale;
        double wave = Math.sin(base + time) * settings.meanderAmplitude;
        double cross = Math.cos((x - z) * settings.meanderFrequency * 0.5 + time * 0.7);
        return Math.toRadians((wave + cross) * 90.0);
    }

    private static int sign(double value) {
        if (value > 0) {
            return 1;
        }
        if (value < 0) {
            return -1;
        }
        return 0;
    }
}
