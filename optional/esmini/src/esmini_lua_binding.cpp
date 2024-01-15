/*
* Copyright 2023 Robert Bosch GmbH
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* SPDX-License-Identifier: Apache-2.0
*/
/**
* \file esmini_lua_binding.cpp
*/

#include "esmini_lua_binding.hpp"

#include <cloe/utility/lua_types.hpp>

#include <fmt/format.h>

#include <string_view>

namespace esmini::lua {
void exportSignals(cloe::DataBroker &dataBroker) {
  cloe::utility::register_lua_types(dataBroker);

  constexpr std::string_view vehicle {"Ego"};

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.acceleration", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.steeringwheel.angle", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = int8_t;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.gearbox.selector", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.gaspedal.position", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.brakepedal.position", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = std::tuple<double, double>;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.front_wheel_angle", vehicle));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

}
}
