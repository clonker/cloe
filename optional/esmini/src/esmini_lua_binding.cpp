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
void exportSignals(cloe::DataBroker &dataBroker, ESMiniVehicle& vehicle) {
  const auto name = vehicle.name();
  cloe::utility::register_lua_types(dataBroker);
  cloe::utility::register_wheel_sensor(dataBroker, name, "fl", [&, val=cloe::Wheel{}]() mutable -> const cloe::Wheel& {
    val=vehicle.get<cloe::WheelSensor>(cloe::CloeComponent::DEFAULT_WHEEL_SENSOR)->wheel_fl();
    return val;
  });
  cloe::utility::register_wheel_sensor(dataBroker, name, "fr", [&, val=cloe::Wheel{}]() mutable -> const cloe::Wheel& {
    val=vehicle.get<cloe::WheelSensor>(cloe::CloeComponent::DEFAULT_WHEEL_SENSOR)->wheel_fr();
    return val;
  });
  cloe::utility::register_wheel_sensor(dataBroker, name, "rl", [&, val=cloe::Wheel{}]() mutable -> const cloe::Wheel& {
    val=vehicle.get<cloe::WheelSensor>(cloe::CloeComponent::DEFAULT_WHEEL_SENSOR)->wheel_rl();
    return val;
  });
  cloe::utility::register_wheel_sensor(dataBroker, name, "rr", [&, val=cloe::Wheel{}]() mutable -> const cloe::Wheel& {
    val=vehicle.get<cloe::WheelSensor>(cloe::CloeComponent::DEFAULT_WHEEL_SENSOR)->wheel_rr();
    return val;
  });

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.acceleration", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.steeringwheel.angle", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = int8_t;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.gearbox.selector", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.gaspedal.position", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = double;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.brakepedal.position", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

  {
    using type = std::tuple<double, double>;
    auto signal = dataBroker.declare<type>(fmt::format("vehicles.{}.actuation.front_wheel_angle", name));
    signal->set_setter<type>([](const type& value) { /*todo*/ });
  }

}
}
