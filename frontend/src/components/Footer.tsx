"use client";

export interface FooterProps {
  /**
   * Primary copyright or brand text on the bottom-left.
   * Defaults to "TalentLens".
   */
  brandText?: string;
  /**
   * Optional custom background color class (defaults to #0066FF).
   */
  className?: string;
  /**
   * Callback or custom handler for legal links.
   */
  onLinkClick?: (linkName: string) => void;
}

const LEGAL_LINKS = [
  { label: "Terms of Service", href: "/" },
  { label: "General Terms and Conditions", href: "/" },
  { label: "Privacy Policy", href: "/" },
  { label: "Cookie Policy", href: "/" },
  { label: "Imprint", href: "/" },
];

const SOCIAL_LINKS = [
  {
    name: "GitHub",
    href: "https://github.com/AveeckPandey",
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path
          fillRule="evenodd"
          clipRule="evenodd"
          d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        />
      </svg>
    ),
  },
  {
    name: "LinkedIn",
    href: "https://www.linkedin.com/in/aveeck-pandey/",
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
      </svg>
    ),
  },
  {
    name: "X (Twitter)",
    href: "https://x.com/BuildWithAveeck",
    icon: (
      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    name: "YouTube",
    href: "https://www.youtube.com/@BuildWithAveeck",
    icon: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
  },
  {
    name: "Instagram",
    href: "https://www.instagram.com/buildwithaveeck/",
    icon: (
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        viewBox="0 0 24 24"
      >
        <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
        <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
      </svg>
    ),
  },
];

export default function Footer({
  brandText = "TalentLens",
  className = "",
  onLinkClick,
}: FooterProps) {
  return (
    <footer className={`w-full mt-16 ${className}`}>
      {/* 
        Organic top wave divider matching remove.bg's wavy SVG boundary.
        Uses brand blue #0066FF to seamlessly blend into the footer body.
      */}
      <div className="w-full overflow-hidden leading-none text-[#0066FF] -mb-[1px] pointer-events-none select-none">
        <svg
          className="w-full h-8 sm:h-12 md:h-16 block"
          viewBox="0 0 1440 36"
          fill="none"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M 0 16 C 95.837 19.991 248.406 28.189 356.852 24.197 C 465.297 20.206 494.295 22.862 640.567 12.208 C 786.839 1.554 804.479 9.552 944.454 12.208 C 1084.43 14.864 1044.06 20.945 1158.81 15.916 C 1273.57 10.888 1440 16 1440 16 L 1440 36 L 0 36 Z"
            fill="currentColor"
          />
        </svg>
      </div>

      {/* Main Footer Body with brand blue #0066FF */}
      <div className="bg-[#0066FF] text-white pt-2 pb-10 sm:pb-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Top Row: Portfolio Button (Left) & Social Media Icons (Right) */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-8 border-b border-white/15">
            {/* Portfolio Pill Button */}
            <div>
              <a
                href="https://portfolio.buildwithaveeck.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white hover:bg-neutral-100 text-[#0066FF] font-bold text-xs sm:text-sm px-5 py-2.5 rounded-full flex items-center gap-2 shadow-sm transition-all duration-150 transform hover:scale-105 active:scale-95"
                aria-label="Visit Portfolio"
              >
                {/* Portfolio Briefcase Icon */}
                <svg
                  className="w-4 h-4 text-[#0066FF]"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  viewBox="0 0 24 24"
                >
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                </svg>
                <span>Portfolio</span>
                {/* Arrow up-right */}
                <svg
                  className="w-3.5 h-3.5 text-[#0066FF]"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 17L17 7M17 7H7M17 7V17" />
                </svg>
              </a>
            </div>

            {/* Social Media Circular Buttons */}
            <div className="flex items-center gap-2.5 sm:gap-3 flex-wrap justify-center">
              {SOCIAL_LINKS.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={item.name}
                  title={item.name}
                  className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-white text-[#0066FF] hover:text-[#0047B3] hover:scale-110 active:scale-95 transition-all duration-150 flex items-center justify-center shadow-sm hover:shadow-md"
                >
                  {item.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Bottom Row: Copyright (Left) & Legal Links (Right) */}
          <div className="flex flex-col-reverse md:flex-row items-center justify-between gap-4 pt-6 text-xs text-white/90">
            {/* Copyright */}
            <div className="text-center md:text-left select-none">
              <p className="m-0 tracking-wide font-medium">© {brandText}</p>
            </div>

            {/* Legal Links */}
            <nav className="flex flex-wrap items-center justify-center md:justify-end gap-x-6 gap-y-2 text-center">
              {LEGAL_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={(e) => {
                    if (onLinkClick) {
                      e.preventDefault();
                      onLinkClick(link.label);
                    }
                  }}
                  className="text-white/85 hover:text-white transition-colors duration-150 hover:underline underline-offset-4"
                >
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
}
