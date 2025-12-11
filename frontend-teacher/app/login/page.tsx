import { LoginForm } from "@/components/login-form"
import { AsciiNoiseEffect } from "@/components/ascii-noise-effect"

export default function LoginPage() {
  return (
    <div className="relative min-h-svh w-full overflow-hidden">
      <AsciiNoiseEffect 
        className="fixed inset-0 z-0"
        speed={0.5}
        cell={10}
        bw={false}
        charset={2}
        brightness={1.5}
        contrast={1.8}
        tint={[1.2, 0.8, 1.5]}
        bg={[0.05, 0, 0.15]}
        hue={180}
        sat={2.0}
        gamma={1.3}
        distortAmp={1.2}
        frequency={12}
        vignette={0.3}
        glyphSharpness={0.08}
      />
      <div className="relative z-10 flex min-h-svh flex-col items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm md:max-w-4xl">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}
