import React from 'react';
import {
  Bars3Icon,
  MagnifyingGlassIcon,
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';

interface HeaderProps {
  onMenuClick: () => void;
  title?: string;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, title = "SCONIA" }) => {
  const userNavigation = [
    { name: 'Your Profile', href: '#' },
    { name: 'Settings', href: '#' },
    { name: 'Kiosk Mode', href: '/kiosk' },
    { name: 'Sign out', href: '#' },
  ];

  return (
    <header className="bg-white shadow-soft border-b border-neutral-200">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 justify-between items-center">
          {/* Left side */}
          <div className="flex items-center">
            <button
              type="button"
              className="btn-ghost p-2 lg:hidden"
              onClick={onMenuClick}
            >
              <span className="sr-only">Open sidebar</span>
              <Bars3Icon className="h-6 w-6" aria-hidden="true" />
            </button>
            
            {/* Logo and title */}
            <div className="flex items-center space-x-3 lg:ml-0 ml-2">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">S</span>
                </div>
              </div>
              <div className="hidden lg:block">
                <h1 className="text-xl font-semibold text-neutral-900">{title}</h1>
                <p className="text-xs text-neutral-500">Supreme Court of Nigeria Information Assistant</p>
              </div>
            </div>
          </div>

          {/* Center - Search (hidden on mobile) */}
          <div className="hidden md:block flex-1 max-w-lg mx-8">
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <MagnifyingGlassIcon className="h-5 w-5 text-neutral-400" aria-hidden="true" />
              </div>
              <input
                type="search"
                placeholder="Search legal documents..."
                className="block w-full rounded-lg border-neutral-300 pl-10 pr-3 py-2 text-sm placeholder-neutral-500 focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Search button for mobile */}
            <button className="btn-ghost p-2 md:hidden">
              <MagnifyingGlassIcon className="h-6 w-6" aria-hidden="true" />
            </button>

            {/* Notifications */}
            <button className="btn-ghost p-2 relative">
              <BellIcon className="h-6 w-6" aria-hidden="true" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-accent-500 rounded-full"></span>
            </button>

            {/* Kiosk Mode */}
            <Link
              to="/kiosk"
              className="btn-ghost p-2 flex items-center space-x-1 text-sm font-medium text-neutral-600 hover:text-primary-600"
              title="Switch to Kiosk Mode"
            >
              <ComputerDesktopIcon className="h-5 w-5" aria-hidden="true" />
              <span className="hidden lg:inline">Kiosk</span>
            </Link>

            {/* Settings */}
            <button className="btn-ghost p-2">
              <Cog6ToothIcon className="h-6 w-6" aria-hidden="true" />
            </button>

            {/* Profile dropdown */}
            <Menu as="div" className="relative">
              <div>
                <Menu.Button className="btn-ghost p-1 rounded-full">
                  <span className="sr-only">Open user menu</span>
                  <UserCircleIcon className="h-8 w-8 text-neutral-600" aria-hidden="true" />
                </Menu.Button>
              </div>
              <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-lg bg-white py-1 shadow-strong ring-1 ring-black ring-opacity-5 focus:outline-none">
                  {userNavigation.map((item) => (
                    <Menu.Item key={item.name}>
                      {({ active }) => (
                        item.href.startsWith('/') ? (
                          <Link
                            to={item.href}
                            className={clsx(
                              active ? 'bg-neutral-100' : '',
                              'block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50'
                            )}
                          >
                            {item.name}
                          </Link>
                        ) : (
                          <a
                            href={item.href}
                            className={clsx(
                              active ? 'bg-neutral-100' : '',
                              'block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50'
                            )}
                          >
                            {item.name}
                          </a>
                        )
                      )}
                    </Menu.Item>
                  ))}
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
