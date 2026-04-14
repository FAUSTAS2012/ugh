package com.example.rivererosion;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;

public class ErosionConfig {
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public int tickInterval = 40;
    public int attemptsPerPlayer = 12;
    public int sampleRadius = 48;
    public double erosionChance = 0.42;

    // Meander behavior (edit these to control river wiggle)
    public double meanderFrequency = 0.06;
    public double meanderAmplitude = 1.8;
    public double meanderTimeScale = 0.003;

    public static ErosionConfig load(Path path) {
        try {
            if (Files.notExists(path.getParent())) {
                Files.createDirectories(path.getParent());
            }

            if (Files.notExists(path)) {
                ErosionConfig config = new ErosionConfig();
                config.save(path);
                return config;
            }

            try (Reader reader = Files.newBufferedReader(path)) {
                ErosionConfig config = GSON.fromJson(reader, ErosionConfig.class);
                return config == null ? new ErosionConfig() : config;
            }
        } catch (IOException e) {
            RiverErosionMod.LOGGER.error("Failed to load config, using defaults", e);
            return new ErosionConfig();
        }
    }

    public void save(Path path) {
        try (Writer writer = Files.newBufferedWriter(path)) {
            GSON.toJson(this, writer);
        } catch (IOException e) {
            RiverErosionMod.LOGGER.error("Failed to save config", e);
        }
    }
}
