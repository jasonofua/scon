import React from 'react';
import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  BookOpenIcon,
  ScaleIcon,
  UserGroupIcon,
  ChartBarIcon,
  XMarkIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import type { NavigationItem } from '../../types';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  currentPath?: string;
}

const navigation: NavigationItem[] = [
  { name: 'Chat', href: '/', icon: ChatBubbleLeftRightIcon, current: true },
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon, current: false },
  { name: 'Documents', href: '/documents', icon: DocumentTextIcon, current: false },
  { name: 'Constitution', href: '/constitution', icon: BookOpenIcon, current: false },
  { name: 'Cases', href: '/cases', icon: ScaleIcon, current: false },
  { name: 'Judges', href: '/judges', icon: UserGroupIcon, current: false },
];

const adminNavigation: NavigationItem[] = [
  { name: 'Analytics', href: '/admin/analytics', icon: ChartBarIcon, current: false },
  { name: 'System Status', href: '/admin/status', icon: ChartBarIcon, current: false },
];



const SidebarContent: React.FC<{ currentPath?: string }> = ({ currentPath }) => {
  const navigate = useNavigate();

  const handleNewChat = () => {
    navigate('/');
    // TODO: Clear current chat session
  };

  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex h-16 flex-shrink-0 items-center px-4 border-b border-neutral-200">
        <Link to="/" className="flex items-center space-x-3">
          <div className="h-8 w-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-neutral-900">SCONIA</h1>
            <p className="text-xs text-neutral-500">Legal Assistant</p>
          </div>
        </Link>
      </div>

      {/* New Chat Button */}
      <div className="px-4 py-4">
        <button
          onClick={handleNewChat}
          className="w-full btn-primary flex items-center justify-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-4 pb-4">
        <div className="space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={clsx(
                currentPath === item.href
                  ? 'bg-primary-50 border-primary-500 text-primary-700'
                  : 'border-transparent text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900',
                'group flex items-center px-3 py-2 text-sm font-medium border-l-4 rounded-r-lg transition-colors duration-200'
              )}
            >
              <item.icon
                className={clsx(
                  currentPath === item.href
                    ? 'text-primary-500'
                    : 'text-neutral-400 group-hover:text-neutral-500',
                  'mr-3 h-5 w-5 flex-shrink-0'
                )}
                aria-hidden="true"
              />
              {item.name}
              {item.badge && (
                <span className="ml-auto inline-block py-0.5 px-2 text-xs rounded-full bg-accent-100 text-accent-800">
                  {item.badge}
                </span>
              )}
            </Link>
          ))}
        </div>



        {/* Admin Section */}
        <div className="pt-6">
          <h3 className="px-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
            Administration
          </h3>
          <div className="mt-2 space-y-1">
            {adminNavigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  currentPath === item.href
                    ? 'bg-secondary-50 border-secondary-500 text-secondary-700'
                    : 'border-transparent text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900',
                  'group flex items-center px-3 py-2 text-sm font-medium border-l-4 rounded-r-lg transition-colors duration-200'
                )}
              >
                <item.icon
                  className={clsx(
                    currentPath === item.href
                      ? 'text-secondary-500'
                      : 'text-neutral-400 group-hover:text-neutral-500',
                    'mr-3 h-5 w-5 flex-shrink-0'
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-neutral-200 p-4">
        <div className="text-xs text-neutral-500 text-center">
          <p>© 2024 Supreme Court of Nigeria</p>
          <p className="mt-1">Version 1.0.0</p>
        </div>
      </div>
    </div>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, currentPath }) => {
  return (
    <>
      {/* Mobile sidebar */}
      <Transition.Root show={open} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-neutral-600 bg-opacity-75" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                    <button type="button" className="-m-2.5 p-2.5" onClick={onClose}>
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white">
                  <SidebarContent currentPath={currentPath} />
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white border-r border-neutral-200 custom-scrollbar">
          <SidebarContent currentPath={currentPath} />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
