package com.example.rivererosion;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.Heightmap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.util.List;

public class RiverErosionMod implements ModInitializer {
    public static final String MOD_ID = "rivererosion";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static final Path CONFIG_PATH = Path.of("config", "river_erosion.json");
    private ErosionConfig config;

    @Override
    public void onInitialize() {
        this.config = ErosionConfig.load(CONFIG_PATH);

        ServerTickEvents.END_SERVER_TICK.register(this::onServerTick);
        LOGGER.info("River Erosion initialized. Edit {} to tune meanders.", CONFIG_PATH);
    }

    private void onServerTick(MinecraftServer server) {
        if (server.getTicks() % Math.max(1, config.tickInterval) != 0) {
            return;
        }

        for (ServerWorld world : server.getWorlds()) {
            List<ServerPlayerEntity> players = world.getPlayers();
            for (ServerPlayerEntity player : players) {
                for (int i = 0; i < config.attemptsPerPlayer; i++) {
                    tryErodeNearPlayer(world, player);
                }
            }
        }
    }

    private void tryErodeNearPlayer(ServerWorld world, ServerPlayerEntity player) {
        if (world.random.nextDouble() > config.erosionChance) {
            return;
        }

        int radius = Math.max(8, config.sampleRadius);
        int x = player.getBlockX() + world.random.nextBetween(-radius, radius);
        int z = player.getBlockZ() + world.random.nextBetween(-radius, radius);
        int y = world.getTopY(Heightmap.Type.MOTION_BLOCKING_NO_LEAVES, x, z) - 1;

        if (y < world.getBottomY() + 2) {
            return;
        }

        BlockPos center = new BlockPos(x, y, z);
        BlockState centerState = world.getBlockState(center);
        if (!centerState.isOf(Blocks.WATER)) {
            return;
        }

        double angle = meanderAngle(world.getTime(), x, z);
        int flowX = (int) Math.signum(Math.cos(angle));
        int flowZ = (int) Math.signum(Math.sin(angle));
        if (flowX == 0 && flowZ == 0) {
            flowX = 1;
        }

        // Perpendicular direction: bank side that gets eroded
        int bankX = -flowZ;
        int bankZ = flowX;

        BlockPos erodePos = center.add(bankX, 0, bankZ);
        BlockState erodeState = world.getBlockState(erodePos);

        if (!isErodible(erodeState)) {
            return;
        }

        world.setBlockState(erodePos, Blocks.WATER.getDefaultState(), Block.NOTIFY_LISTENERS);

        // Simple deposition on opposite bank to enhance visible meander drift
        BlockPos depositPos = center.add(-bankX, 0, -bankZ);
        BlockState depositState = world.getBlockState(depositPos);
        if (depositState.isAir() || depositState.isIn(BlockTags.DIRT)) {
            world.setBlockState(depositPos, Blocks.SAND.getDefaultState(), Block.NOTIFY_LISTENERS);
        }

        // Keep top layer hydrated for a smoother bank shape
        BlockPos above = erodePos.up();
        if (!world.getBlockState(above).isAir()) {
            world.breakBlock(above, true);
        }
    }

    private boolean isErodible(BlockState state) {
        return state.isIn(BlockTags.DIRT)
                || state.isIn(BlockTags.SAND)
                || state.isOf(Blocks.GRASS_BLOCK)
                || state.isOf(Blocks.CLAY)
                || state.isOf(Blocks.GRAVEL);
    }

    private double meanderAngle(long worldTime, int x, int z) {
        double base = (x + z) * config.meanderFrequency;
        double time = worldTime * config.meanderTimeScale;
        double wave = Math.sin(base + time) * config.meanderAmplitude;
        double cross = Math.cos((x - z) * config.meanderFrequency * 0.5 + time * 0.7);
        return MathHelper.wrapDegrees((float) ((wave + cross) * 90.0)) * (Math.PI / 180.0) + Direction.EAST.asRotation();
    }
}
