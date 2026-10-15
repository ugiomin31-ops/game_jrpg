// 심연의 미궁 — stylised toon shader for URP 17 (Unity 6.3).
// Colour comes from mesh vertex colour ("Col" in Blender) * _BaseColor (* optional _BaseMap).
// Features: banded main light + soft secondary band, received shadows, additional lights (Forward+/cluster),
// rim light, emission, world-space colour noise (breaks up flat environment colours), inverted-hull outline,
// hit flash (_FlashColor.a) and dissolve (_Dissolve 0..1) driven from scripts via MaterialPropertyBlock.
Shader "Abyss/Toon"
{
    Properties
    {
        _BaseColor ("Base Colour", Color) = (1,1,1,1)
        [NoScaleOffset] _BaseMap ("Base Map (optional)", 2D) = "white" {}
        _ShadowTint ("Shadow Tint", Color) = (0.42,0.40,0.62,1)
        _ShadowThreshold ("Shadow Threshold", Range(-1,1)) = 0.05
        _ShadowSoftness ("Shadow Softness", Range(0.001,0.5)) = 0.06
        _MidBand ("Mid Band Strength", Range(0,1)) = 0.25
        _RimColor ("Rim Colour", Color) = (1,0.95,0.85,1)
        _RimStrength ("Rim Strength", Range(0,2)) = 0.35
        _RimPower ("Rim Power", Range(0.5,8)) = 3.5
        _Specular ("Toon Specular", Range(0,1)) = 0.12
        _EmissionStrength ("Emission Strength", Range(0,10)) = 0
        _NoiseStrength ("World Noise Strength", Range(0,0.5)) = 0
        _NoiseScale ("World Noise Scale", Float) = 1.6
        _Alpha ("Alpha", Range(0,1)) = 1
        _OutlineWidth ("Outline Width", Range(0,0.05)) = 0.012
        _OutlineColor ("Outline Colour", Color) = (0.10,0.07,0.12,1)
        _FlashColor ("Flash Colour (a = amount)", Color) = (1,1,1,0)
        _Dissolve ("Dissolve", Range(0,1)) = 0
        _DissolveEdge ("Dissolve Edge Colour", Color) = (1,0.55,0.2,1)
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Src Blend", Float) = 1
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Dst Blend", Float) = 0
        [Enum(Off,0,On,1)] _ZWrite ("ZWrite", Float) = 1
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor;
            half4 _ShadowTint;
            half _ShadowThreshold;
            half _ShadowSoftness;
            half _MidBand;
            half4 _RimColor;
            half _RimStrength;
            half _RimPower;
            half _Specular;
            half _EmissionStrength;
            half _NoiseStrength;
            float _NoiseScale;
            half _Alpha;
            float _OutlineWidth;
            half4 _OutlineColor;
            half4 _FlashColor;
            half _Dissolve;
            half4 _DissolveEdge;
        CBUFFER_END

        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);

        float Hash31(float3 p)
        {
            p = frac(p * 0.1031);
            p += dot(p, p.zyx + 31.32);
            return frac((p.x + p.y) * p.z);
        }

        float ValueNoise(float3 p)
        {
            float3 i = floor(p);
            float3 f = frac(p);
            f = f * f * (3.0 - 2.0 * f);
            float n000 = Hash31(i), n100 = Hash31(i + float3(1,0,0));
            float n010 = Hash31(i + float3(0,1,0)), n110 = Hash31(i + float3(1,1,0));
            float n001 = Hash31(i + float3(0,0,1)), n101 = Hash31(i + float3(1,0,1));
            float n011 = Hash31(i + float3(0,1,1)), n111 = Hash31(i + float3(1,1,1));
            return lerp(lerp(lerp(n000, n100, f.x), lerp(n010, n110, f.x), f.y),
                        lerp(lerp(n001, n101, f.x), lerp(n011, n111, f.x), f.y), f.z);
        }

        // Object-space dissolve so the pattern sticks to the character while it moves.
        void ClipDissolve(float3 positionOS, out half edge)
        {
            edge = 0;
            if (_Dissolve > 0.001)
            {
                float n = ValueNoise(positionOS * 9.0) * 0.65 + ValueNoise(positionOS * 23.0) * 0.35;
                float d = n - _Dissolve * 1.05;
                clip(d);
                edge = 1.0 - saturate(d / 0.06);
            }
        }
        ENDHLSL

        Pass
        {
            Name "ForwardToon"
            Tags { "LightMode"="UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                half4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                half4 color : TEXCOORD2;
                float2 uv : TEXCOORD3;
                float3 positionOS : TEXCOORD4;
                half fogFactor : TEXCOORD5;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.color = v.color;
                o.uv = v.uv;
                o.positionOS = v.positionOS.xyz;
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half3 ToonLight(Light light, half3 albedo, half3 n, half3 viewDir, half ao)
            {
                half ndl = dot(n, light.direction);
                half atten = light.shadowAttenuation * light.distanceAttenuation;
                half lit = smoothstep(_ShadowThreshold - _ShadowSoftness, _ShadowThreshold + _ShadowSoftness, ndl);
                half mid = smoothstep(0.55 - _ShadowSoftness, 0.55 + _ShadowSoftness, ndl) * _MidBand;
                lit = min(lit, smoothstep(0.35, 0.65, light.shadowAttenuation)) * light.distanceAttenuation;
                half3 shade = lerp(albedo * _ShadowTint.rgb, albedo * (1.0 + mid), lit);
                half3 h = normalize(light.direction + viewDir);
                half spec = smoothstep(0.92, 0.95, dot(n, h)) * _Specular * lit;
                return (shade + spec) * light.color * ao;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                half edge;
                ClipDissolve(i.positionOS, edge);

                half4 baseTex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv);
                half3 albedo = i.color.rgb * _BaseColor.rgb * baseTex.rgb;
                if (_NoiseStrength > 0.001)
                {
                    float nz = ValueNoise(i.positionWS * _NoiseScale) * 0.6 + ValueNoise(i.positionWS * _NoiseScale * 3.7) * 0.4;
                    albedo *= 1.0 + (nz - 0.5) * 2.0 * _NoiseStrength;
                }

                half3 n = normalize(i.normalWS);
                half3 viewDir = GetWorldSpaceNormalizeViewDir(i.positionWS);

                InputData inputData = (InputData)0;
                inputData.positionWS = i.positionWS;
                inputData.normalWS = n;
                inputData.viewDirectionWS = viewDir;
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                inputData.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                half ao = 1;
                #if defined(_SCREEN_SPACE_OCCLUSION)
                    AmbientOcclusionFactor aoF = GetScreenSpaceAmbientOcclusion(inputData.normalizedScreenSpaceUV);
                    ao = lerp(1, aoF.directAmbientOcclusion, 0.6);
                #endif

                half4 shadowMask = half4(1,1,1,1);
                Light mainLight = GetMainLight(inputData.shadowCoord, i.positionWS, shadowMask);
                half3 color = ToonLight(mainLight, albedo, n, viewDir, ao);

                // Ambient: flat-ish SH so the dark side keeps colour instead of going black.
                half3 sh = SampleSH(n);
                color += albedo * sh * 0.55 * ao;

                #if defined(_ADDITIONAL_LIGHTS)
                    uint pixelLightCount = GetAdditionalLightsCount();
                    LIGHT_LOOP_BEGIN(pixelLightCount)
                        Light light = GetAdditionalLight(lightIndex, i.positionWS, shadowMask);
                        half ndl = saturate(dot(n, light.direction));
                        half band = smoothstep(0.0, 0.12, ndl) * 0.75 + 0.25;
                        color += albedo * light.color * light.distanceAttenuation * light.shadowAttenuation * band;
                    LIGHT_LOOP_END
                #endif

                half rim = pow(saturate(1.0 - dot(n, viewDir)), _RimPower) * _RimStrength;
                rim *= saturate(dot(n, mainLight.direction) * 0.5 + 0.6);
                color += _RimColor.rgb * rim * mainLight.color;

                color += albedo * _EmissionStrength;
                color = lerp(color, _FlashColor.rgb, _FlashColor.a);
                color = lerp(color, _DissolveEdge.rgb * 4.0, edge);
                color = MixFog(color, i.fogFactor);
                return half4(color, _Alpha * i.color.a * _BaseColor.a);
            }
            ENDHLSL
        }

        Pass
        {
            Name "Outline"
            Tags { "LightMode"="SRPDefaultUnlit" }
            Cull Front
            ZWrite [_ZWrite]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionOS : TEXCOORD0; half fogFactor : TEXCOORD1; half4 color : TEXCOORD2; };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                float4 cs = TransformObjectToHClip(v.positionOS.xyz);
                float3 nCS = mul((float3x3)UNITY_MATRIX_VP, TransformObjectToWorldNormal(v.normalOS));
                // Screen-space constant width, clamped so distant objects don't get fat outlines.
                float2 offset = normalize(nCS.xy + 1e-5) * _OutlineWidth * min(cs.w, 6.0);
                offset.x *= _ScreenParams.y / _ScreenParams.x;
                cs.xy += offset * step(0.0001, _OutlineWidth);
                o.positionCS = cs;
                o.positionOS = v.positionOS.xyz;
                o.fogFactor = ComputeFogFactor(cs.z);
                o.color = v.color;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half edge;
                ClipDissolve(i.positionOS, edge);
                clip(_OutlineWidth - 0.0001);
                clip(_Alpha - 0.99);
                half3 c = _OutlineColor.rgb * lerp(half3(1,1,1), i.color.rgb, 0.35);
                return half4(MixFog(c, i.fogFactor), 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull Back

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionOS : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                float3 positionWS = TransformObjectToWorld(v.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(v.normalOS);
                #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                    float3 lightDirectionWS = normalize(_LightPosition - positionWS);
                #else
                    float3 lightDirectionWS = _LightDirection;
                #endif
                float4 cs = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDirectionWS));
                cs = ApplyShadowClamping(cs);
                o.positionCS = cs;
                o.positionOS = v.positionOS.xyz;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half edge;
                ClipDissolve(i.positionOS, edge);
                clip(_Alpha - 0.5);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On
            ColorMask R

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionOS : TEXCOORD0; };
            Varyings vert(Attributes v) { Varyings o; UNITY_SETUP_INSTANCE_ID(v); o.positionCS = TransformObjectToHClip(v.positionOS.xyz); o.positionOS = v.positionOS.xyz; return o; }
            half frag(Varyings i) : SV_Target { half e; ClipDissolve(i.positionOS, e); clip(_Alpha - 0.5); return i.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode"="DepthNormals" }
            ZWrite On

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float3 positionOS : TEXCOORD1; };
            Varyings vert(Attributes v) { Varyings o; UNITY_SETUP_INSTANCE_ID(v); o.positionCS = TransformObjectToHClip(v.positionOS.xyz); o.normalWS = TransformObjectToWorldNormal(v.normalOS); o.positionOS = v.positionOS.xyz; return o; }
            half4 frag(Varyings i) : SV_Target { half e; ClipDissolve(i.positionOS, e); clip(_Alpha - 0.5); return half4(NormalizeNormalPerPixel(i.normalWS), 0); }
            ENDHLSL
        }
    }
    FallBack "Hidden/Universal Render Pipeline/FallbackError"
}
