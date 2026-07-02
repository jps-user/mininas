#!/usr/bin/perl
package main;
BEGIN { push(@INC, ".."); };
use WebminCore;
use Encode qw(decode_utf8);
&init_config();
&ReadParse();
$main::default_charset = 'utf-8';
require 'mininas/mininas-lib.pl';
require 'mininas/ui_components.pl';

my $sec_name = $in{'section'};
my ($lines_ref, $sections_ref) = parse_smb_sections_v2();
my ($target) = grep { $_->{name} eq $sec_name } @$sections_ref;

if (!$target) {
    &WebminCore::ui_print_header(undef, "Error", "", undef, 0, 0);
    print mn_head()."<div class='mn-wrap'><p style='color:var(--mn-red);'>Section not found.</p></div>";
    &WebminCore::ui_print_footer("index.cgi", "Back"); exit;
}

&WebminCore::ui_print_header(undef, "Edit Share", "", undef, 0, 0);
print mn_head();
print "<div class='mn-wrap'>";
print "<div class='mn-page-header'><a class='mn-page-back' href='index.cgi'><i class='ti ti-arrow-left'></i> Dashboard</a><span class='mn-page-title'>Edit: $sec_name</span></div>";

my $raw = Encode::decode_utf8($target->{raw});
$raw = join("\n", map { s/^\s+//r } split(/\n/, $raw));

my ($f_path,$f_writable,$f_browsable) = ("","yes","yes");
my (@f_rw,@f_ro,@leftover);

foreach my $line (split(/\n/, $raw)) {
    if    ($line =~ /^\s*path\s*=\s*(.+)/i)        { $f_path=  $1; $f_path     =~ s/^\s+|\s+$//g; }
    elsif ($line =~ /^\s*writable\s*=\s*(.+)/i)    { $f_writable = lc($1); $f_writable =~ s/^\s+|\s+$//g; }
    elsif ($line =~ /^\s*browsable\s*=\s*(.+)/i)   { $f_browsable= lc($1); $f_browsable=~ s/^\s+|\s+$//g; }
    elsif ($line =~ /^\s*valid users\s*=\s*(.+)/i) { my $u=$1; $u=~s/^\s+|\s+$//g; push(@f_rw,$u) if $u; }
    elsif ($line =~ /^\s*read list\s*=\s*(.+)/i)   { my $u=$1; $u=~s/^\s+|\s+$//g; push(@f_ro,$u) if $u; }
    else  { push(@leftover, $line) if ($line=~/\S/ || @leftover); }
}
while (@leftover && $leftover[-1] !~ /\S/) { pop @leftover; }
my $leftover_text = join("\n", map { s/^\s+//; $_ } @leftover);
my $rw_users = join("\n", @f_rw);
my $ro_users = join("\n", @f_ro);
my $is_global = ($sec_name eq 'global');

print "<form action='save_section.cgi' method='post'>";
print &WebminCore::ui_hidden("old_section", $sec_name);

if ($is_global) {
    print "<div class='mn-form-wrap'>";
    print "<div class='mn-form-title'><i class='ti ti-world' style='margin-right:6px; color:var(--mn-muted);'></i>Global settings – raw editor<span style='font-size:11px; color:var(--mn-muted); margin-left:10px;'>Direct smb.conf edit, no filesystem actions</span></div>";
    print "<textarea class='mn-textarea' name='raw_extra' rows='20'>".&WebminCore::html_escape($raw)."</textarea>";
    print "</div>";
} else {
    # Block 1: Strukturierte Felder
    print "<div class='mn-form-wrap'>";
    print "<div class='mn-form-title'><i class='ti ti-settings' style='margin-right:6px; color:var(--mn-muted);'></i>Share settings<span style='font-size:11px; color:var(--mn-muted); margin-left:10px;'>Changes here may trigger filesystem actions</span></div>";

    print "<div class='mn-form-row'>";
    print "<div class='mn-form-col'><label class='mn-label'>Share name</label><input class='mn-input' type='text' name='section' value='".&WebminCore::html_escape($sec_name)."'></div>";
    print "<div class='mn-form-col' style='flex:2;'><label class='mn-label'>Path</label><input class='mn-input' type='text' name='f_path' value='".&WebminCore::html_escape($f_path)."'></div>";
    print "<div class='mn-form-col'><label class='mn-label'>If path changed</label><select class='mn-select' name='path_action'><option value='none'>No action</option><option value='mkdir'>Create directory</option><option value='rename'>Move/rename</option></select></div>";
    print "</div>";

    my $wr = ($f_writable eq 'yes')  ? 'checked' : '';
    my $br = ($f_browsable eq 'yes') ? 'checked' : '';
    print "<div class='mn-check-row'>";
    print "<label class='mn-check-label'><input type='checkbox' name='f_writable'  value='yes' $wr> Writable</label>";
    print "<label class='mn-check-label'><input type='checkbox' name='f_browsable' value='yes' $br> Browsable</label>";
    print "</div>";

    print "<div class='mn-form-row'>";
    print "<div class='mn-form-col'><label class='mn-label'><i class='ti ti-circle-filled' style='color:var(--mn-green); font-size:10px;'></i> Read/Write users (valid users)</label><textarea class='mn-textarea' name='f_valid_rw' rows='4' placeholder='one username per line'>".&WebminCore::html_escape($rw_users)."</textarea><div class='mn-hint'>One per line. New OS users must be created via provisioning form.</div></div>";
    print "<div class='mn-form-col'><label class='mn-label'><i class='ti ti-circle-filled' style='color:var(--mn-amber); font-size:10px;'></i> Read-only users (read list)</label><textarea class='mn-textarea' name='f_valid_ro' rows='4' placeholder='one username per line'>".&WebminCore::html_escape($ro_users)."</textarea><div class='mn-hint'>Listed users get read-only access.</div></div>";
    print "</div>";
    print "</div>";

    # Block 2: Raw
    print "<div class='mn-form-wrap'>";
    print "<div class='mn-form-title'><i class='ti ti-code' style='margin-right:6px; color:var(--mn-muted);'></i>Advanced / raw parameters<span style='font-size:11px; color:var(--mn-muted); margin-left:10px;'>smb.conf only – no filesystem actions. Tab = 4 spaces.</span></div>";
    print "<div class='mn-hint' style='margin-bottom:10px;'>Add Samba-specific options: <code>fruit:</code>, <code>vfs objects</code>, <code>comment</code>, <code>create mask</code>, etc.</div>";
    print "<textarea class='mn-textarea' name='raw_extra' rows='8' id='raw_ta' placeholder='vfs objects = catia fruit streams_xattr\nfruit:time machine = yes'>".&WebminCore::html_escape($leftover_text)."</textarea>";
    print "</div>";
}

print "<div style='display:flex; gap:10px; margin-top:4px;'>";
print "<button type='submit' name='action' value='save' class='mn-btn mn-btn-primary'><i class='ti ti-device-floppy'></i> Save share</button>";
print "<a href='index.cgi' class='mn-btn'><i class='ti ti-x'></i> Cancel</a>";
print "</div></form>";

# Tab → 4 Spaces
print "<script>document.getElementById('raw_ta') && document.getElementById('raw_ta').addEventListener('keydown',function(e){if(e.key==='Tab'){e.preventDefault();var s=this.selectionStart,en=this.selectionEnd,v=this.value;this.value=v.substring(0,s)+'    '+v.substring(en);this.selectionStart=this.selectionEnd=s+4;}});</script>";

print "</div>";
&WebminCore::ui_print_footer("index.cgi", "Back to Dashboard");
