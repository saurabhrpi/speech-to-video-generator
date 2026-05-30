---
name: reference_fabric_circle_image_absolutefill
description: On New Arch (Fabric), an absoluteFill cover Image inside a rounded overflow:hidden wrapper anchors to the top; size the Image directly instead
metadata:
  type: reference
---

**Symptom:** a circular avatar/thumbnail renders showing only the TOP of the source image (e.g. plain background above a face) instead of the cover-centered middle — looks like an "empty" circle.

**Cause:** with `newArchEnabled: true` (Fabric, this app), this pattern misbehaves — the `absoluteFill` Image anchors to the top rather than cover-centering inside the rounded clip:
```
<View style={{width:76,height:76,borderRadius:38,overflow:'hidden'}}>
  <Image source={x} style={StyleSheet.absoluteFill} resizeMode="cover" />
</View>
```

**Fix:** put size + radius DIRECTLY on the `<Image>`, no wrapper (the canonical RN avatar pattern):
```
<Image source={x} style={{width:76,height:76,borderRadius:38,borderWidth:2.5,borderColor:'#fff'}} resizeMode="cover" />
```

**Debugging note that saved time (S86 onboarding "Before" circles):** when an overwritten/bundled image renders wrong, FIRST `Read` the file on disk to confirm its content + dimensions are correct. Here the file was a perfect 704×704 face, which ruled out a Metro asset-cache / same-name-overwrite stale theory — renaming the asset did NOT fix it — and pointed at rendering. Don't assume stale-asset-cache; verify the bytes first.
