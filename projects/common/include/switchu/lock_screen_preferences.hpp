#pragma once
#include <nlohmann/json.hpp>
#include <switchu/frontend_style.hpp>
#include <filesystem>
#include <fstream>
#include <string>

namespace switchu::lock_screen {
inline bool enabled() {
    std::string frontend;
    std::getline(std::ifstream("sdmc:/config/SwitchU/frontend.txt"), frontend);
    if (switchu::parseFrontendStyle(frontend) != switchu::FrontendStyle::WiiU) {
        std::ifstream in("sdmc:/config/CardsNX/settings.json");
        const auto settings = nlohmann::json::parse(in, nullptr, false);
        if (!settings.is_object()) return false;
        const auto at = settings.find("lockScreen");
        return at != settings.end() && at->is_boolean() && at->get<bool>();
    }
    std::error_code ec;
    return std::filesystem::exists("sdmc:/config/SwitchU/lock_screen", ec);
}
}
