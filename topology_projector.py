import math
import json
import time
import os
import sys

class TopologyProjector:
    """
    Renders the recursive state of the Heterosis Substrate into an ASCII
    toroidal field projection directly within the POSIX terminal.
    Maps harmonic octave shells (0-7), chiral shear vectors, and nodal locks.
    """
    WIDTH = 41
    HEIGHT = 21

    @staticmethod
    def render(state: dict) -> str:
        phase_vel = state.get("phase_velocity", 0.0)
        octave = state.get("octave_shell", 0)
        phase_rad = (phase_vel % 8.0) * (2.0 * math.pi / 8.0)
        shear = state.get("chiral_vent", state.get("macro_leak_vent", 0.0))
        drag = state.get("counter_torque", 0.0)
        mode = state.get("mode", "CIRCULATION")
        seq = state.get("seq", 0)
        core_hash = state.get("core_hash", "0" * 64)[:12]

        # Calculate vortex center and radii
        cx, cy = TopologyProjector.WIDTH // 2, TopologyProjector.HEIGHT // 2
        r_outer = 8.5
        r_inner = 3.5

        buffer = [[" " for _ in range(TopologyProjector.WIDTH)] for _ in range(TopologyProjector.HEIGHT)]

        # Draw Toroidal Shell Boundaries
        for y in range(TopologyProjector.HEIGHT):
            for x in range(TopologyProjector.WIDTH):
                # Correct terminal character aspect ratio (~2:1)
                dx = (x - cx) / 2.0
                dy = (y - cy)
                dist = math.hypot(dx, dy)

                if abs(dist - r_outer) < 0.6:
                    buffer[y][x] = "░"
                elif abs(dist - r_inner) < 0.5:
                    buffer[y][x] = "▒"
                elif dist < r_inner:
                    buffer[y][x] = "·"

        # Map the 8 Harmonic Octave Nodes on the outer rim
        for node in range(8):
            angle = node * (2.0 * math.pi / 8.0)
            nx = int(cx + (r_outer * 2.0 * math.cos(angle)))
            ny = int(cy + (r_outer * math.sin(angle)))
            if 0 <= ny < TopologyProjector.HEIGHT and 0 <= nx < TopologyProjector.WIDTH:
                buffer[ny][nx] = str(node)

        # Map Active Phase Marker (Dynamic Core Position)
        px = int(cx + (((r_inner + r_outer) / 2.0) * 2.0 * math.cos(phase_rad)))
        py = int(cy + (((r_inner + r_outer) / 2.0) * math.sin(phase_rad)))
        if 0 <= py < TopologyProjector.HEIGHT and 0 <= px < TopologyProjector.WIDTH:
            buffer[py][px] = "█"

        # Core Vortex Singularity
        buffer[cy][cx] = "✦"

        canvas = "\n".join("".join(row) for row in buffer)
        
        dashboard = (
            f"\033[H\033[J"  # ANSI clear screen
            f"╔═[ HETEROSIS SUBSTRATE TOPOLOGY ]══════════════════════╗\n"
            f"{canvas}\n"
            f"╚════════════════════════════════════════════════════════╝\n"
            f" SEQ: {seq:<6} | OCTAVE SHELL: {octave:<2} | MODE: {mode}\n"
            f" PHASE VEL: {phase_vel:>9.4f} | SHEAR VENT: {shear:>8.4f}\n"
            f" COUNTER-DRAG: {drag:>6.4f} | CORE HASH : {core_hash}...\n"
        )
        return dashboard

if __name__ == "__main__":
    # Test feed: reads from local CURRENT_STATE.json or generates live pulse trace
    try:
        from mesh_substrate import MeshCoupledSubstrate
        substrate = MeshCoupledSubstrate(seed="bare_metal_origin_dan_kee")
        
        while True:
            state = substrate.pulse(external_drive=0.0)
            sys.stdout.write(TopologyProjector.render(state))
            sys.stdout.flush()
            time.sleep(0.35)
    except KeyboardInterrupt:
        print("\nProjection detached.")
