#include <switchu/frontend_style.hpp>
#include <cassert>
#include <string>

int main() {
    using namespace switchu;
    assert(parseFrontendStyle("homenx") == FrontendStyle::WiiU);
    assert(parseFrontendStyle("cards") == FrontendStyle::Cards);
    assert(parseFrontendStyle("cards-xmb") == FrontendStyle::Xmb);
    assert(parseFrontendStyle("xmb") == FrontendStyle::Xmb);
    assert(parseFrontendStyle("") == FrontendStyle::Xmb);
    assert(parseFrontendStyle("unknown") == FrontendStyle::WiiU);
    for (auto style : {FrontendStyle::WiiU, FrontendStyle::Cards, FrontendStyle::Xmb})
        assert(parseFrontendStyle(frontendValue(style)) == style);
    // Existing daemon resume behavior recognizes both non-grid frontends.
    assert(std::string(frontendValue(FrontendStyle::Xmb)).starts_with("cards"));
    assert(std::string(frontendValue(FrontendStyle::Cards)).starts_with("cards"));
    assert(!std::string(frontendValue(FrontendStyle::WiiU)).starts_with("cards"));
}
