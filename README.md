# OrangeFox Recovery for OnePlus Nord N100 (`billie2`)

Device tree for building OrangeFox Recovery R12.0 (fox_12.1 branch) for the
OnePlus Nord N100, built entirely on GitHub Actions.

## Device

| Feature | Specification |
| :-- | :-- |
| Codename | `billie2` |
| Model | BE2013 (OnePlus Nord N100) |
| SoC | Qualcomm SM4250 Snapdragon 460 |
| Display | 720x1600, 6.52" |
| Storage | UFS 2.1, A/B with a dedicated recovery partition |
| Shipping Android | 11 (OxygenOS 11.0.15, OTA 14.E.35) |
| Encryption | FBE + metadata encryption (f2fs userdata) |

## Layout

- `BoardConfig.mk`, `device.mk`, `twrp_billie2.mk`, `fox_billie2.mk` - build config
- `recovery/root` - recovery ramdisk overlay (QTI keymaster/gatekeeper/qseecomd)
- `prebuilt` - prebuilt kernel, dtb and dtbo
- `tools/unpack_boot.py` - Android boot image unpacker used by CI

## Build

The `build-orangefox.yml` workflow syncs the OrangeFox manifest and builds:

```
export FOX_BUILD_DEVICE=billie2
lunch twrp_billie2-eng
mka adbd recoveryimage
```

Builds are produced as `OrangeFox-*.zip` and `recovery.img` artifacts.

## Credits

- TeamWin Recovery Project
- OrangeFox Recovery Project
- Royna2544 for the original TWRP device tree for `billie2`
