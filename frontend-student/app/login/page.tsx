import { LoginForm } from "@/components/login-form"
import { AsciiNoiseEffect } from "@/components/ascii-noise-effect"

export default function LoginPage() {
  return (
    <div className="relative flex min-h-svh flex-col items-center justify-center p-6 md:p-10 overflow-hidden">
      <AsciiNoiseEffect
        className="absolute inset-0 z-0"
        speed={0.5}
        cell={10}
        charset={2}
        brightness={1.5}
        contrast={1.8}
        sat={2.0}
        tint={[1.2, 0.8, 1.5]}
        hue={120}
        bg={[0.05, 0, 0.15]}
        distortAmp={1.2}
        frequency={12}
        vignette={0.3}
      />
      <div className="w-full max-w-sm md:max-w-4xl z-10">
        <LoginForm />
      </div>
    </div>
  )
}
