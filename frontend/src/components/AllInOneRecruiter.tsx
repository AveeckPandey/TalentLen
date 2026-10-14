"use client";

export default function AllInOneRecruiter() {
  return (
    <section className="py-12 sm:py-20">
      <div className="max-w-6xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
          
          {/* Left Column: Headline and Description (remove.bg style) */}
          <div className="lg:col-span-7 space-y-5 text-left">
            <h2 className="text-3xl sm:text-4xl lg:text-[42px] font-extrabold text-neutral-900 dark:text-white tracking-tight leading-[1.18]">
              All-in-one AI Recruiter
            </h2>

            <p className="text-base sm:text-lg text-neutral-600 dark:text-neutral-300 leading-relaxed">
              TalentLens is your go-to, high-quality candidate finder, making it easy to{" "}
              <strong className="text-neutral-900 dark:text-white font-semibold">
                scan out of hundreds of resumes
              </strong>{" "}
              and isolate the best candidates with incredible accuracy.
            </p>

            <p className="text-sm sm:text-base text-neutral-500 dark:text-neutral-400 leading-relaxed">
              Whether you&apos;re hiring for{" "}
              <strong className="text-neutral-900 dark:text-white font-semibold">
                Full-Stack, AI &amp; Machine Learning, Data Analysis, Cloud &amp; DevOps
              </strong>
              , or Software Engineering—TalentLens evaluates authentic project complexity, problem solving, and technical depth with zero human bias.
            </p>


          </div>

          {/* Right Column: Rounded Card with Cute 3D Robot Mascot (Image-1) */}
          <div className="lg:col-span-5 flex justify-center lg:justify-end">
            <div className="w-full max-w-md rounded-3xl bg-neutral-100 dark:bg-neutral-900 border border-neutral-200/90 dark:border-neutral-800 p-8 sm:p-10 flex flex-col items-center justify-center shadow-xl dark:shadow-2xl/40 relative overflow-hidden group">
              {/* Subtle ambient gradient backdrop */}
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />

              <div className="relative z-10 w-full max-w-[280px] sm:max-w-[320px] flex items-center justify-center">
                <img
                  src="/ai-recruiter-robot.png"
                  alt="TalentLens AI Recruiter Assistant"
                  className="w-full h-auto object-contain drop-shadow-2xl select-none transform transition-transform duration-300 group-hover:scale-105"
                />
              </div>

              <div className="relative z-10 mt-5 text-center">
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  AI Recruiter Active
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
