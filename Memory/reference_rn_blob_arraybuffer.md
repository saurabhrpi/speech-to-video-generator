---
name: RN Blob has no arrayBuffer()
description: React Native's Blob doesn't support .arrayBuffer(); use File.downloadFileAsync for saving remote files to disk
type: reference
---

React Native's `Blob` does not implement `.arrayBuffer()` — calling it throws "blob.arrayBuffer is not a function (it is undefined)".

To download a remote file to local disk, use expo-file-system's `File.downloadFileAsync(url, directory)` which streams directly on the native side without needing blob/buffer intermediaries.

```ts
import { File, Directory, Paths } from 'expo-file-system';
const dest = new Directory(Paths.cache, 'videos');
if (!dest.exists) dest.create();
const file = await File.downloadFileAsync(videoUrl, dest);
// file.uri is now a local path
```
