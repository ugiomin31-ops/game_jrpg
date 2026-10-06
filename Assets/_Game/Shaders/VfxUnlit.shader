// Anime-style ("cel") VFX shader. Texture alpha is the shape; RGB is optional shading.
// _Cel 1: the shape is posterised into crisp bands, the hottest band burns white on additive layers (HDR, so
// bloom catches it; "hottest" = solid in a small neighbourhood, so thin strokes keep the tint), and fading erodes the shape from its soft edge inward instead of turning it translucent.
// _Cel 0 reproduces the original soft multiply (texture * vertex colour * tint).
Shader "Abyss/VfxUnlit"
{
    Properties
    {
        _MainTex ("Shape / Flipbook", 2D) = "white" {}
        [HDR] _Tint ("Tint", Color) = (1,1,1,1)
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Destination Blend", Float) = 1
        _Cel ("Cel Look (0 soft, 1 anime)", Range(0,1)) = 1
        _Bands ("Shape Bands", Range(1,6)) = 3
        _CoreStart ("White Core Start", Range(0,1)) = 0.72
        _CoreRadius ("White Core Probe Radius (UV)", Range(0,0.05)) = 0.014
        _Intensity ("Additive HDR Intensity", Range(0,4)) = 1.6
        _Additive ("Additive Layer (set by VfxLibrary)", Float) = 1
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        Pass
        {
            Name "Vfx"
            Tags { "LightMode"="UniversalForward" }
            Blend SrcAlpha [_DstBlend]
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                half4 _Tint;
                half _Cel;
                half _Bands;
                half _CoreStart;
                float _CoreRadius;
                half _Intensity;
                half _Additive;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; half4 color : COLOR; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; half4 color : COLOR; float2 uv : TEXCOORD0; UNITY_VERTEX_OUTPUT_STEREO };
            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                output.color = input.color * _Tint;
                output.uv = TRANSFORM_TEX(input.uv, _MainTex);
                return output;
            }

            // Posterises v (0..1) into _Bands steps with a one-pixel anti-aliased rise at each step.
            half Bands(half v)
            {
                half q = v * _Bands;
                half aa = max(fwidth(q), 1e-3);
                return (floor(q) + smoothstep(1.0 - aa, 1.0, frac(q))) / _Bands;
            }

            half4 Frag(Varyings input) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv);
                half4 soft = tex * input.color;
                if (_Cel < 0.001) return soft;

                half fade = saturate(input.color.a);
                // Erosion: as the layer fades, the cut-off climbs so thin halo parts vanish first.
                half threshold = (1.0 - fade) * 0.85;
                half shape = saturate((tex.a - threshold) / max(1.0 - threshold, 1e-3));
                half banded = Bands(shape);
                half alpha = banded * saturate(fade * 3.0);

                half3 rgb;
                if (_Additive > 0.5)
                {
                    // Solid interiors burn white-hot; strokes thinner than the probe radius keep the saturated tint.
                    float2 d = float2(_CoreRadius, -_CoreRadius);
                    half solid = (SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv + d.xx).a
                                + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv + d.xy).a
                                + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv + d.yx).a
                                + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv + d.yy).a) * 0.25;
                    half heat = banded * min(tex.r, solid);
                    half core = smoothstep(_CoreStart, 1.0, heat);
                    rgb = lerp(input.color.rgb, half3(1, 1, 1) + input.color.rgb * 0.25, core) * _Intensity;
                }
                else
                {
                    // Alpha-blended puffs and icons: two-tone cel shading of the texture's own shading.
                    half lum = dot(tex.rgb, half3(0.299, 0.587, 0.114));
                    // Light and mid tones snap to two flat levels; dark ink (icon outlines) stays as authored.
                    half toon = lum > 0.55 ? 1.05 : (lum > 0.25 ? 0.62 : lum);
                    rgb = input.color.rgb * lerp(tex.rgb, toon * (tex.rgb / max(lum, 1e-3)), 0.75);
                }
                return lerp(soft, half4(rgb, alpha), _Cel);
            }
            ENDHLSL
        }
    }
}
