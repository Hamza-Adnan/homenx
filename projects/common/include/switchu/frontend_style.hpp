#pragma once
#include <string_view>

namespace switchu {
enum class FrontendStyle { WiiU, Cards, Xmb };
inline FrontendStyle parseFrontendStyle(std::string_view value) {
    if (value.empty() || value == "xmb" || value.starts_with("cards-xmb")) return FrontendStyle::Xmb;
    if (value.starts_with("cards")) return FrontendStyle::Cards;
    return FrontendStyle::WiiU;
}
inline const char* frontendValue(FrontendStyle style) {
    // Retain the cards prefix understood by the daemon's resume policy.
    switch (style) {
        case FrontendStyle::Xmb: return "cards-xmb";
        case FrontendStyle::Cards: return "cards";
        default: return "homenx";
    }
}
inline const char* frontendName(FrontendStyle style) {
    switch (style) {
        case FrontendStyle::Xmb: return "XMB NX";
        case FrontendStyle::Cards: return "CardsNX";
        default: return "Wii U";
    }
}
}
