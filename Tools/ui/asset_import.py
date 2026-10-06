"""Write Unity texture import settings without launching the editor; preserve existing asset GUIDs."""
import pathlib
import re
import uuid


def texture_meta(path, sprite=False, border=(0, 0, 0, 0), repeat=False):
    path = pathlib.Path(path)
    meta = pathlib.Path(str(path) + '.meta')
    existing = meta.read_text(encoding='utf-8') if meta.exists() else ''
    match = re.search(r'^guid: ([0-9a-f]+)', existing, re.MULTILINE)
    guid = match.group(1) if match else uuid.uuid5(uuid.NAMESPACE_URL, 'abyss:' + path.name + ':' + path.parent.name).hex
    left, bottom, right, top = border
    content = f'''fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  isReadable: 0
  streamingMipmaps: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: {0 if repeat else 1}
    wrapV: {0 if repeat else 1}
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: {1 if sprite else 0}
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: 100
  spriteBorder: {{x: {left}, y: {bottom}, z: {right}, w: {top}}}
  spriteGenerateFallbackPhysicsShape: 0
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: {8 if sprite else 0}
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  platformSettings:
  - serializedVersion: 3
    buildTarget: DefaultTexturePlatform
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 0
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: {uuid.uuid5(uuid.NAMESPACE_URL, 'abyss:sprite:' + path.name).hex}
    internalID: 0
    vertices: []
    indices:
    edges: []
    weights: []
    secondaryTextures: []
  userData:
  assetBundleName:
  assetBundleVariant:
'''
    meta.write_text(content, encoding='utf-8', newline='\n')
