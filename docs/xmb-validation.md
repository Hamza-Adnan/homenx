# XMB validation — November 9, 2026

## Passed locally

- `tests/xmb_navigation_test.cpp`: compiled with native GCC and executed successfully (exit 0). Covers empty and single-item lists, selection limits, long libraries, selection anchoring, fractional scroll geometry and category/touch alignment.
- `projects/cards/src/CardsActivity.cpp`: devkitA64 C++20 `-fsyntax-only` check passed with `NXUI_BACKEND_DEKO3D` for standalone and `SWITCHU_MENU` configurations using installed libnx and official dependency headers.
- `projects/manager/src/ManagerActivity.cpp`: devkitA64 C++20 production-backend syntax check passed.
- `git diff --check`: passed.
- Inspected the illustrative 1280 × 720 desktop preview for spacing, hierarchy and clipping. The preview uses sample titles, original HomeNX icons and approximated desktop text rendering. It is not an on-console screenshot.

## Not completed

GitHub Actions run [42697072345](https://github.com/Hamza-Adnan/homenx/actions/runs/42697072345) did not allocate runners. GitHub reported: “The job was not started because your account is locked due to a billing issue.” Neither compilation job executed. Re-run the Build HomeNX workflow after resolving the account issue.

A local standalone build subsequently compiled, linked and packaged successfully using devkitA64 GCC 16.1.0, libnx 4.12.0, deko3d 0.5.0 and the pinned SDL audout package. `CardsNX.nro` includes its RomFS assets. The ELF is AArch64 and has no unresolved symbols. The NRO/ASET headers and embedded icon/NACP/RomFS bounds were checked.

- NRO size: 12,324,658 bytes.
- SHA-256: `fc79d71535a1b431f9c01fa64f75286582bff288778bc047d7ce6f3e43f478d5`.
- UI source revision: `db059e7`.
- Build helper: `scripts/build_cards_local.py`, using nlohmann/json 3.10.5.

The full HOME replacement package has not been linked/built locally. Physical Switch testing remains outstanding for runtime services, inputs, launch/return behavior, rendering performance and installation.

## Hardware checks after building

1. Try `CardsNX.nro` through hbmenu/Sphaira and verify all four categories, a large library, an empty category and custom/hidden categories.
2. Check D-pad and both sticks, held Up/Down repeat, ZL/ZR, toolbar access with Y/B, options/reordering, quick settings and touch swipe/tap behavior.
3. Launch and resume software, return HOME and open system applets in the HOME replacement build.
4. Verify saved Wii U preferences, new-install XMB selection, lock/wake behavior and motion disabled settings.

The upstream three-start frontend fallback and SD recovery method remain in place.

## Fluid motion revision (smooth-2)

The user confirmed that the initial standalone NRO works on their Switch. The revised animation feel still needs their on-device comparison.

- Exact critically damped springs preserve velocity across interrupted/repeated inputs. Animation timing uses elapsed frame time (bounded after long stalls).
- Category positions, glyph sizes and brightness move continuously; previous/current software columns slide and crossfade over 280 ms.
- Item icons, names, detail opacity and focus rings share one continuous focus curve instead of snapping to the selected index.
- Holding Left/Right repeats category navigation. Touch hit testing follows the animated rail and active column.
- Full-screen blur is only captured for visible frosted overlays, avoiding that GPU pass on ordinary browsing frames.
- Native tests passed: frame-rate equivalence at 30/60/120 Hz, monotonic settling, rapid retargeting, reversal, long held input, navigation bounds and touch geometry.
- Standalone NRO compiled, linked and packaged; HOME configuration passed the Switch compiler syntax check. Physical frame timing has not been measured.

NRO SHA-256: `903561a70db4ad4d3280bde4d05ef1ed00a2be0ac44da5066c7c5f893d06d2fa`.
NRO size: 12332850 bytes. Build label: `local XMB smooth-2` / `1.2.0-xmb2`.
