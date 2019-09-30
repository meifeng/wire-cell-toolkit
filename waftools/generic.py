#!/usr/bin/env python
'''
This is NOT a waf tool but generic functions to be called from a waf
tool, in particular by wcb.py.

There's probably a wafier way to do this.

The interpretation of options are very specific so don't change them
unless you really know all the use cases.  The rules are:

If package is optional:

    - omitting all --with-NAME* options will omit use the package

    - explicitly using --with-NAME=false (or "no" or "off") will omit
      use of the package.

If package is mandatory:

    - omitting all --with-NAME* options will use pkg-config to find
      the package.

    - explicitly using --with-NAME=false (or "no" or "off") will
      assert.

In either case:

    - explicitly using --with-NAME=true (or "yes" or "on") will use
      pkg-config to find the package.

    - using --with-NAME* with a path will attempt to locate the
      package without using pkg-config

Note, actually, pgk-config fails often to do its job.  Best to always
use explicit --with-NAME=[<bool>|<dir>].
'''

import os.path as osp
def _options(opt, name):
    lower = name.lower()
    opt = opt.add_option_group('%s Options' % name)
    opt.add_option('--with-%s'%lower, type='string', default=None,
                   help="give %s installation location" % name)
    opt.add_option('--with-%s-include'%lower, type='string', 
                   help="give %s include installation location"%name)
    opt.add_option('--with-%s-lib'%lower, type='string', 
                   help="give %s lib installation location"%name)
    return

def _configure(ctx, name, incs=(), libs=(), bins=(), pcname=None, mandatory=True):
    lower = name.lower()
    UPPER = name.upper()
    if pcname is None:
        pcname = lower

    instdir = getattr(ctx.options, 'with_'+lower, None)
    incdir = getattr(ctx.options, 'with_%s_include'%lower, None)
    libdir = getattr(ctx.options, 'with_%s_lib'%lower, None)
    bindir = getattr(ctx.options, 'with_%s_bin'%lower, None)
    #print ("CONFIGURE", name, inst,inc,lib, mandatory)

    if mandatory:
        if instdir:
            assert (instdir.lower() not in ['no','off','false'])
    else:                       # optional
        # if not any([instdir, incdir, libdir]):
        #     print ("skipping non mandatory %s, use --with-%s=[yes|<dir>] to force" % (name, lower))
        #     return
        if instdir and instdir.lower() in ['no','off','false']:
            return

    # rely on package config
    if not any([instdir,incdir,libdir,bindir]) or (instdir and instdir.lower() in ['yes','on','true']):
        ctx.start_msg('Checking for %s in PKG_CONFIG_PATH' % name)
        args = "--cflags"
        if libs:                # things like eigen may not have libs
            args += " --libs"
        ctx.check_cfg(package=pcname,  uselib_store=UPPER,
                      args=args, mandatory=mandatory)
        if 'HAVE_'+UPPER in ctx.env:
            ctx.end_msg("found")
        else:
            ctx.end_msg("failed")
            return
    else:                       # do manual setting

        if incs:
            if not incdir and instdir:
                incdir = osp.join(instdir, 'include')
            if incdir:
                setattr(ctx.env, 'INCLUDES_'+UPPER, [incdir])

        if libs:
            if not libdir and instdir:
                libdir = osp.join(instdir, 'lib')
            if libdir:
                setattr(ctx.env, 'LIBPATH_'+UPPER, [libdir])

        if bins:
            if not bindir and instdir:
                bindir = osp.join(instdir, 'bin')
            if libdir:
                setattr(ctx.env, 'PATH_'+UPPER, [bindir])
            
    
    # now check, this does some extra work in the caseof pkg-config

    if libs:
        ctx.start_msg("Location for %s libs" % name)
        for tryl in libs:
            ctx.check_cxx(lib=tryl,
                          use=UPPER, uselib_store=UPPER, mandatory=mandatory)
        ctx.end_msg(str(getattr(ctx.env, 'LIBPATH_' + UPPER, None)))

        ctx.start_msg("Libs for %s" % name)
        ctx.end_msg(str(getattr(ctx.env, 'LIB_' + UPPER)))

    if incs:
        ctx.start_msg("Location for %s headers" % name)
        for tryh in incs:
            ctx.check_cxx(header_name=tryh,
                          use=UPPER, uselib_store=UPPER, mandatory=mandatory)
        ctx.end_msg(str(getattr(ctx.env, 'INCLUDES_' + UPPER, None)))

    if bins:
        ctx.start_msg("Bins for %s" % name)
        found_bins = list()
        for tryb in bins:
            ctx.find_program(tryb, var=tryb.upper(), mandatory=mandatory)
            found_bins += ctx.env[tryb.upper()]
        ctx.end_msg(str(found_bins))

